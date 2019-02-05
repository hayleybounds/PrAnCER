# -*- coding: utf-8 -*-
"""
Created on Tue Apr 24 15:02:10 2018

@author: rdb_lab
"""
import unittest
import pandas as pd
from PrAnCER import combine_prints, assign_print_numbers, create_combo_prints
import numpy as np

class TestCombination(unittest.TestCase):

    def setUp(self):
        self.ex_df = pd.DataFrame( {'print_numb':[1,2,3,4,5,10],
        'max_area':[30,40,10,22,40,5],
        'X':[5,6,8,9,10,12],'Y':[55,10,66,70,62,77],'first_frame':[0,0,3,1,12,14],
        'last_frame':[4,5,14,11,18,20],
        'is_right':[True,True,True,True,True,True],
        'is_hind':[False,False,False,False,False,False],
        'frame_max_a':[2,3,5,6,14,15]})

        self.ex_df_varied = pd.DataFrame( {'print_numb':[1,2,3,4,5,10],
        'max_area':[30,40,10,22,40,5],
        'X':[5,6,8,9,10,12],'Y':[55,10,66,70,62,77],'first_frame':[0,0,3,4,12,14],
        'last_frame':[4,5,9,11,18,20],
        'is_right':[True,False,True,False,True,False],
        'is_hind':[False,False,True,False,True,False],
        'frame_max_a':[2,3,5,6,14,15]})

    def test_max_idx_kept(self):
        combine_prints(self.ex_df, 0, 1)
        self.assertTrue(1 in self.ex_df.index.values)
        self.assertFalse(0 in self.ex_df.index.values)
        combine_prints(self.ex_df, 1, 5)
        self.assertTrue(5 in self.ex_df.index.values)
        self.assertFalse(1 in self.ex_df.index.values)
        self.assertTrue(10 in self.ex_df.print_numb.values)
        self.assertFalse(2 in self.ex_df.print_numb.values)

    def test_max_area_stats_kept_keep_idx_and_big_diff(self):
        #when big_idx and keep_idx are different
        self.assertTrue(self.ex_df.max_area[2]==10)
        self.assertTrue(self.ex_df.X[2]==8)
        self.assertTrue(self.ex_df.Y[2]==66)
        self.assertTrue(self.ex_df.frame_max_a[2]==5)

        combine_prints(self.ex_df, 1, 2)

        self.assertTrue(self.ex_df.max_area[2]==40)
        self.assertTrue(self.ex_df.X[2]==6)
        self.assertTrue(self.ex_df.Y[2]==10)
        self.assertTrue(self.ex_df.frame_max_a[2]==3)

    def test_max_area_stats_kept_keep_idx_and_big_same(self):
        #when big_idx and keep_idx are the same
        self.assertTrue(self.ex_df.max_area[3]==22)
        self.assertTrue(self.ex_df.X[3]==9)
        self.assertTrue(self.ex_df.Y[3]==70)
        self.assertTrue(self.ex_df.frame_max_a[3]==6)

        combine_prints(self.ex_df, 2, 3)

        self.assertTrue(self.ex_df.max_area[3]==22)
        self.assertTrue(self.ex_df.X[3]==9)
        self.assertTrue(self.ex_df.Y[3]==70)
        self.assertTrue(self.ex_df.frame_max_a[3]==6)

    def test_frame_combos(self):
        #test that the frame range is always the minimum to the maximum
        combine_prints(self.ex_df, 4, 5)
        self.assertTrue(self.ex_df.first_frame[5] == 12)
        self.assertTrue(self.ex_df.last_frame[5] == 20)
        #check with odd ordering of first and last
        combine_prints(self.ex_df, 2, 3)
        self.assertTrue(self.ex_df.first_frame[3] == 1)
        self.assertTrue(self.ex_df.last_frame[3] == 14)
        
    def test_no_combine_different_classes(self):
        with self.assertRaises(ValueError):
            combine_prints(self.ex_df_varied,4,5)


class TestPrintNumberAssignment(unittest.TestCase):
    def setUp(self):
        self.df = pd.DataFrame({'is_kept': [True, True, True], 'X': [4,7,8],
                      'Y': [40, 43, 41], 'frame': [1,2,3]})
    
    def test_assign_same(self):
        #test that hulls meeting criteria for the same paw are given same #
        assign_print_numbers(self.df, 5)
        self.assertEqual(self.df.print_numb.unique(), [1])
    
    def test_assign_diff_numbers_dist(self):
        #test that prints that are further than same_dist are different numbers
        self.df['Y'] = [40, 43, 54]
        assign_print_numbers(self.df, 5)
        self.assertEqual(len(self.df.print_numb.unique()), 2)
        self.assertEqual(self.df.print_numb[0], self.df.print_numb[1])
        self.assertNotEqual(self.df.print_numb[1], self.df.print_numb[2])
    
    def test_assign_diff_numbers_frame(self):
        #test prints within same dist but more than 1 frame apart are diff
        self.df['frame'] = [1,2,4]
        assign_print_numbers(self.df, 5)
        self.assertEqual(len(self.df.print_numb.unique()), 2)
        self.assertEqual(self.df.print_numb[0], self.df.print_numb[1])
        self.assertNotEqual(self.df.print_numb[1], self.df.print_numb[2])
    
    def test_assign_diff_numbers_dist_reverse(self):
        #test that if the middle one is too far from the first but the third
        #is close enough, they're still given different numbers
        self.df.Y = [40, 46, 42]
        assign_print_numbers(self.df, 5)
        self.assertEqual(len(self.df.print_numb.unique()), 2)
        self.assertNotEqual(self.df.print_numb[0], self.df.print_numb[1])
        self.assertEqual(self.df.print_numb[1], self.df.print_numb[2])
        
    def test_assign_to_closest(self):
        #test the print is assigned to the closest match
        self.df['frame'] = [1,1,2]
        assign_print_numbers(self.df, 5)
        self.assertEqual(len(self.df.print_numb.unique()), 2)
        self.assertNotEqual(self.df.print_numb[0], self.df.print_numb[1])
        self.assertNotEqual(self.df.print_numb[0], self.df.print_numb[2])
        self.assertEqual(self.df.print_numb[1], self.df.print_numb[2])
        
    def test_assign_diff_numbers_same_frame(self):
        #test that it resolves duplicate assignment within the same frame
        self.df['frame'] = [1,2,2]
        assign_print_numbers(self.df, 5)
        self.assertEqual(len(self.df.print_numb.unique()), 2)
        self.assertNotEqual(self.df.print_numb[0], self.df.print_numb[1])
        self.assertNotEqual(self.df.print_numb[1], self.df.print_numb[2])
        self.assertEqual(self.df.print_numb[0], self.df.print_numb[2])
        
    def test_no_assign_not_kept(self):
        #test that if a hull is not kept, it is not assigned a number
        self.df['is_kept'] = [True, False, True]
        assign_print_numbers(self.df, 5)
        self.assertEqual(len(self.df.print_numb.unique()), 3)
        self.assertNotEqual(self.df.print_numb[0], self.df.print_numb[2])
        self.assertTrue(np.isnan(self.df.print_numb[1]))
        
    def test_more_complex_case(self):
        #test a more realistic dataframe, taken from a real run
        c_df = pd.read_pickle('tester hull.p')
        old_print_numbs = c_df.print_numb.values
        assign_print_numbers(c_df, 20)
        self.assertEqual(c_df.print_numb.values.all(), old_print_numbs.all())
        
        
class TestCreateComboPrints(unittest.TestCase):
    """tests that create combo prints correctly summarizes info and correctly
    assigns front/hind paws. Also tests the helper method assign left/right.
    """
    
    def setUp(self):
        self.hulls_df = pd.DataFrame({'X': [400,474,484, 40, 44, 47],
                      'Y': [40, 43, 41, 200, 203, 206],
                      'frame': [1,2,3, 5,6,7],
                      'area': [100, 40, 30, 120, 300, 150],
                      'print_numb': [1,1,1,2,2,2]})
        self.hulls_df['is_kept'] = True
    
    def test_info_is_from_hull_with_max_area(self):
        combo_prints = create_combo_prints(self.hulls_df, 5, 600)
        assert np.array_equal(combo_prints.max_area, [100, 300])
        assert np.array_equal(combo_prints.frame_max_a, [1,6])
        assert np.array_equal(combo_prints.X, [400, 44])
        assert np.array_equal(combo_prints.Y, [40, 203])
    
    def test_frame_range_correct(self):
        combo_prints = create_combo_prints(self.hulls_df, 5, 600)
        assert np.array_equal(combo_prints.first_frame, [1,5])
        assert np.array_equal(combo_prints.last_frame, [3,7])
    
    def test_left_right_correct(self):
        combo_prints = create_combo_prints(self.hulls_df, 5, 600)
        assert np.array_equal(combo_prints.is_right, [False, True])
    
    def test_front_hind_simple(self):
        f_h_df = pd.DataFrame({'X': [20, 30, 70], 'Y': [300, 60, 210],
                               'area': [50, 50, 50], 'frame': [8,9,10],
                               'print_numb': [3,4,5]})
        f_h_df['is_kept'] = True
        f_h_df = self.hulls_df.append(f_h_df, ignore_index=True)
        combo_prints = create_combo_prints(f_h_df, 5, 600)
        assert np.array_equal(combo_prints.is_hind,
                              [False, False, False, True, True])
    
    def test_front_hind_same_frame_prints(self):
        f_h_df = pd.DataFrame({'X': [20, 30, 70, 20, 10],
                               'Y': [300, 60, 210, 40, 60],
                               'area': [50, 50, 50,50,50],
                               'frame': [8,9,10,10,10],
                               'print_numb': [3,4,5,6,7]})
        f_h_df['is_kept'] = True
        f_h_df = self.hulls_df.append(f_h_df, ignore_index=True)
        combo_prints = create_combo_prints(f_h_df, 5, 600)
        self.assertEqual(combo_prints.is_hind[5], True)
        self.assertEqual(combo_prints.is_hind[6], True)
        self.assertEqual(combo_prints.is_hind[7], False)
        self.assertEqual(combo_prints.is_hind[4], True)
        
    def test_front_hind_w_scrambled_order(self):
        f_h_df = pd.DataFrame({'X': [20, 30, 70], 'Y': [300, 60, 210],
                               'area': [50, 50, 50], 'frame': [10, 8, 9],
                               'print_numb': [3,4,5]})
        f_h_df['is_kept'] = True
        f_h_df = self.hulls_df.append(f_h_df, ignore_index=True)
        combo_prints = create_combo_prints(f_h_df, 5, 600)
        assert np.array_equal(combo_prints.sort_values(['print_numb']).is_hind,
                              [False, False, False, False, True])
        
    def test_left_right_simple(self):
        f_h_df = pd.DataFrame({'X': [20, 30, 70, 20, 10],
                               'Y': [300, 60, 210, 40, 60],
                               'area': [50, 50, 50,50,50],
                               'frame': [8,9,10,10,10],
                               'print_numb': [3,4,5,6,7]})
        f_h_df['is_kept'] = True
        f_h_df = self.hulls_df.append(f_h_df, ignore_index=True)
        combo_prints = create_combo_prints(f_h_df, 5, 600)
        assert np.array_equal(combo_prints.sort_values(['print_numb']).is_right,
                              [False, True, True, False, True, False, False])
        
    def test_real_example(self):
        #test a more realistic dataframe, taken from a real run
        #TODO: match combo_prints and hulls bc currently y is different
        c_df = pd.read_pickle('tester hull.p')
        assign_print_numbers(c_df, 20)
        key = pd.read_csv('tester combo df.csv')
        combo_prints = create_combo_prints(c_df, 20, 1920)
        combo_prints.sort_values('print_numb', inplace=True)
        assert np.array_equal(combo_prints.astype('int').X.values.sort(),
                              key.X.values.sort())

class TestFindMatchesAndCombine(unittest.TestCase):
    """combine has already been tested, so only needs to check that the correct
    matches are found.
    """
    
    
    
if __name__ == '__main__':
    unittest.main()