# -*- coding: utf-8 -*-
"""
Created on Wed Mar 28 20:30:27 2018


Modified from PIMS source code to work on my machine. Basically, made demuzers
and such only read video frames and not audio.
"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


import numpy as np

from pims.base_frames import FramesSequence
from pims.frame import Frame

from warnings import warn


try:
    import av
except ImportError:
    av = None


def available():
    return av is not None


def _to_nd_array(frame):
    if frame.format.name != 'rgb24':
        frame = frame.reformat(format="rgb24")
    frame_arr = np.frombuffer(frame.planes[0], np.uint8)
    frame_arr.shape = (frame.height, frame.width, -1)
    return frame_arr


class WrapPyAvFrame(object):
    def __init__(self, frame, frame_no, metadata=None):
        self.frame_no = frame_no
        self.arr = None
        self.metadata = metadata

        # makes a copy of the frame so that ffmpeg does not reuse the buffer
        # by converting already to rgb24. rgb24 movies actually are converted
        # twice. don't know how to just copy! But the operations are fast.
        if frame.format.name == 'rgb24':
            frame = frame.reformat(format="bgr24")
        self.frame = frame.reformat(format="rgb24")

    def to_frame(self):
        if self.arr is None:
            self.arr = Frame(_to_nd_array(self.frame), frame_no=self.frame_no,
                             metadata=self.metadata)
        return self.arr


def _gen_frames(demuxer, time_base, frame_rate=1., first_pts=0):
    for packet in demuxer:
        for frame in packet.decode():
            # learn timestamp
            for timestamp in (frame.pts, packet.pts, frame.dts, packet.dts):
                if timestamp is not None:
                    break
            else:
                raise IOError(
                    "Unable to read video: frames contain no timestamps. "
                    "Please use PyAVReaderIndexed.")
            t = (timestamp - first_pts) * time_base
            i = int(t * frame_rate)
            yield WrapPyAvFrame(frame, frame_no=i,
                                metadata=dict(timestamp=timestamp, t=float(t)))


class PyAVReaderTimed(FramesSequence):
    """Read images from a video file via a direct FFmpeg/AVbin interface.
    The frames are indexed according to their 'timestamp', starting at 0 at the
    timestamp of the first non-empty frame. Missing frames are filled in with
    empty frames. The number of frames in the video is estimated from the
    movie duration and the average frame rate.
    Parameters
    ----------
    filename : string
    cache_size : integer, optional
        the number of frames that are kept in memory. Default 16.
    fast_forward_thresh : integer, optional
        the reader will proceed through the frames if forwarding below this
        number. If forwarding above this number, it will use seek(). Default 32.
    stream_index : integer, optional
        the index of the video stream inside the file. rarely other than 0.
    Examples
    --------
    >>> video = PyAVVideoReader('video.avi')  # or .mov, etc.
    >>> video[0] # Show the first frame.
    >>> video[-1] # Show the last frame.
    >>> video[1][0:10, 0:10] # Show one corner of the second frame.
    >>> for frame in video[:]:
    ...    # Do something with every frame.
    >>> for frame in video[10:20]:
    ...    # Do something with frames 10-20.
    >>> for frame in video[[5, 7, 13]]:
    ...    # Do something with frames 5, 7, and 13.
    >>> frame_count = len(video) # Number of frames in video
    >>> frame_shape = video.frame_shape # Pixel dimensions of video
    """
    class_priority = 9
    @classmethod
    def class_exts(cls):
        return {'mov', 'avi', 'mp4'} | super(PyAVReaderTimed, cls).class_exts()

    def __init__(self, filename, cache_size=16, fast_forward_thresh=32,
                 stream_index=0):
        self.filename = str(filename)
        self._container = av.open(self.filename)

        if len(self._container.streams.video) == 0:
            raise IOError("No valid video stream found in {}".format(filename))

        self._stream = self._container.streams.video[stream_index]

        try:
            self._duration = self._stream.duration * self._stream.time_base
        except TypeError:
            self._duration = self._container.duration / av.time_base

        self._frame_rate = self._stream.average_rate
        if self.duration <= 0 or len(self) <= 0:
            raise IOError("Video stream {} in {} has zero length.".format(stream_index, filename))

        self._cache = [None] * cache_size
        self._fast_forward_thresh = fast_forward_thresh

        demuxer = self._container.demux(streams=self._stream)

        # obtain first frame to get first time point
        # also tests for the presence of timestamps
        frame = next(_gen_frames(demuxer, self._stream.time_base))
        self._first_pts = frame.metadata['timestamp']

        frame = WrapPyAvFrame(frame.frame, 0, frame.metadata)
        self._cache[0] = frame
        self._frame_shape = (self._stream.height, self._stream.width, 3)
        self._last_frame = 0

        self._reset_demuxer()

    def __len__(self):
        return int(self._duration * self._frame_rate)

    def _reset_demuxer(self):
        demuxer = self._container.demux(streams=self._stream)
        self._frame_generator = _gen_frames(demuxer, self._stream.time_base,
                                            self._frame_rate, self._first_pts)

    @property
    def duration(self):
        """The video duration in seconds."""
        return float(self._duration)

    @property
    def frame_shape(self):
        return self._frame_shape

    @property
    def frame_rate(self):
        return float(self._frame_rate)

    def get_frame(self, i):
        cached_frame = self._cache[i % len(self._cache)]
        if cached_frame is None:
            cached_i = -1
        else:
            cached_i = cached_frame.frame_no

        # return directly if the frame is in cache
        if cached_i == i:
            return cached_frame.to_frame()

        # check if we will have to seek to the frame
        if self._last_frame >= i or \
            self._last_frame < i - self._fast_forward_thresh:
            frame = self.seek(i)

            # return directly if the seek was perfect (happens rarely)
            if frame is not None:
                if frame.frame_no == i:
                    return frame.to_frame()

        # proceed through the frames
        result = None
        for frame in self._frame_generator:
            # first cache the frame
            self._cache[frame.frame_no % len(self._cache)] = frame
            self._last_frame = frame.frame_no

            if frame.frame_no < i:
                continue  # go on towards the frame
            elif frame.frame_no == i:
                result = frame
                break
            else:  # the frame was not inside the reader
                break
        else:
            # always restart the frame generator when it ends
            self._reset_demuxer()

        if result is None:
            # the requested frame actually does not exist. Can occur due to
            # a bad file, or due to inaccuracy of reader length __len__.
            # find it in the cache
            for other_i in range(i - 1, i - len(self._cache), -1):
                result = self._cache[other_i % len(self._cache)]
                if result is None:
                    continue
                if result.frame_no < i:
                    break
            else:  # cache is empty: return an empty frame
                return Frame(np.zeros(self.frame_shape, dtype=self.pixel_type),
                             frame_no=i)

        return result.to_frame()

    def seek(self, i):
        """Seek to a frame before i and return the first frame."""
        # flush the cache
        self._cache = [None] * len(self._cache)
        # the ffmpeg decode cache is flushed automatically

        timestamp = int(i / (self._frame_rate * self._stream.time_base))
        self._stream.seek(timestamp + self._first_pts)

        # check the first frame
        try:
            frame = next(self._frame_generator)
        except StopIteration:
            self._reset_demuxer()
            try:
                frame = next(self._frame_generator)
            except StopIteration:
                return None

        if i == 0:  # security measure to avoid infinite recursion
            return frame

        if frame.frame_no > i:
            # recurse with an additional offset of 16 frames
            return self.seek(i - 16)

        # add the frame to the cache if succesful
        self._cache[frame.frame_no % len(self._cache)] = frame
        self._last_frame = frame.frame_no
        return frame

    @property
    def pixel_type(self):
        return np.uint8

    def __repr__(self):
        # May be overwritten by subclasses
        return """<Frames>
Format: {format}
Source: {filename}
Duration: {duration:.3f} seconds
Frame rate: {frame_rate:.3f} fps
Length: {count} frames
Frame Shape: {frame_shape!r}
""".format(frame_shape=self.frame_shape,
           format=self._stream.long_name,
           duration=self.duration,
           frame_rate=self.frame_rate,
           count=len(self),
           filename=self.filename)


class PyAVReaderIndexed(FramesSequence):
    """Read images from the frames of a standard video file into an
    iterable object that returns images as numpy arrays.
    Parameters
    ----------
    filename : string
    Examples
    --------
    >>> video = Video('video.avi')  # or .mov, etc.
    >>> imshow(video[0]) # Show the first frame.
    >>> imshow(video[-1]) # Show the last frame.
    >>> imshow(video[1][0:10, 0:10]) # Show one corner of the second frame.
    >>> for frame in video[:]:
    ...    # Do something with every frame.
    >>> for frame in video[10:20]:
    ...    # Do something with frames 10-20.
    >>> for frame in video[[5, 7, 13]]:
    ...    # Do something with frames 5, 7, and 13.
    >>> frame_count = len(video) # Number of frames in video
    >>> frame_shape = video.frame_shape # Pixel dimensions of video
    """
    class_priority = 8

    @classmethod
    def class_exts(cls):
        return {'mov', 'avi',
                'mp4'} | super(PyAVReaderIndexed, cls).class_exts()

    def __init__(self, filename):
        self.filename = str(filename)
        self._initialize()

    def _initialize(self):
        "Scan through and tabulate contents to enable random access."
        container = av.open(self.filename)

        # Build a toc
        self._toc = np.cumsum([len(packet.decode())
                               for packet in container.demux(video=0)])
        self._len = self._toc[-1]

        video_stream = [s for s in container.streams
                        if isinstance(s, av.video.VideoStream)][0]
        # PyAV always returns frames in color, and we make that
        # assumption in get_frame() later below, so 3 is hardcoded here:
        self._im_sz = video_stream.height, video_stream.width, 3

        del container  # The generator is empty. Reload the file.
        self._load_fresh_file()

    def _load_fresh_file(self):
        self._demuxed_container = av.open(self.filename).demux(video=0)
        self._current_packet = next(self._demuxed_container).decode()
        self._packet_cursor = 0
        self._frame_cursor = 0

    def __len__(self):
        return self._len

    @property
    def frame_shape(self):
        return self._im_sz

    def get_frame(self, j):
        # Find the packet this frame is in.
        packet_no = self._toc.searchsorted(j, side='right')
        self._seek_packet(packet_no)
        # Find the location of the frame within the packet.
        if packet_no == 0:
            loc = j
        else:
            loc = j - self._toc[packet_no - 1]
        frame = self._current_packet[loc]  # av.VideoFrame
        if frame.index != j:
            raise AssertionError("Seeking failed to obtain the correct frame.")
        result = _to_nd_array(frame)
        return Frame(result, frame_no=j)

    def _seek_packet(self, packet_no):
        """Advance through the container generator until we get the packet
        we want. Store that packet in selfpp._current_packet."""
        if packet_no == self._packet_cursor:
            # We have the right packet and it is already decoded.
            return
        if packet_no < self._packet_cursor:
            # "Rewind." This is not really possible, so we load a fresh
            # instance of the file object and then fast-forward.
            self._load_fresh_file()
        # Fast-forward if needed.
        while self._packet_cursor < packet_no:
            self._current_packet = next(self._demuxed_container).decode()
            self._packet_cursor += 1

    @property
    def pixel_type(self):
        # No need to detect dtype: PyAV always returns uint8.
        return np.uint8

    def __repr__(self):
        # May be overwritten by subclasses
        return """<Frames>
Source: {filename}
Length: {count} frames
Frame Shape: {frame_shape!r}
""".format(frame_shape=self.frame_shape,
           count=len(self),
           filename=self.filename)