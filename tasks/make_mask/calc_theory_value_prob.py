#!/usr/bin/env python
# -*- coding: utf-8 -*-
import scipy.misc as scm
import numpy as np
import itertools


def one_line_check(mask_num, one_line_pattern, location_dots):
    alive_dots = location_dots[:]
    for num in mask_num:
        try:
            alive_dots.remove(num)
        except:
            continue
    for pattern in one_line_pattern:
        match_num = 0
        for num in alive_dots:
            if num in pattern:
                match_num += 1
        if match_num > 2:
            return True
    return False


def calc_probability(n, k, p):
    prob = 0.0
    for i in range(k, n + 1):
        prob += scm.comb(n, i) * (p ** i) * ((1 - p) ** (n - i))
    return prob


if __name__ == '__main__':
    mask_area_file = open("./datas/csv/mask_area_paired.csv", "r")
    mask_num_lines = mask_area_file.readlines()
    mask_num_list = [mask_num_lines[i].split(",")[:-1] for i in range(len(mask_num_lines))]
    mask_num_list.insert(0, [])  # for no masking
    read_prob = 0.95
    # convert to int
    for i in range(len(mask_num_list)):
        for j in range(len(mask_num_list[i])):
            mask_num_list[i][j] = int(mask_num_list[i][j])
    # result file
    theory_result = open("./datas/csv/theory_result.csv", "w")

    location_dots = [0, 3, 6, 9, 12, 14, 17, 20]
    information_dots = [1, 2, 4, 5, 7, 8, 10, 11, 13, 15, 16, 18, 19, 21, 22]
    # one_line_pattern = [[0, 3, 6], [12, 14, 17]]
    one_line_pattern = [[0, 3, 6], [12, 14, 17], [6, 9, 12], [0, 17, 20]]

    # real world accuracy
    real_one = [1, 1, 1, 1, 1, 1, 0.99, 0.99, 0.93, 0.77, 0.42, 0.073]
    real_two = [1, 1, 1, 0.99, 0.99, 0.97, 0.92, 0.84, 0.68, 0.33]

    # prob_candidates = list(itertools.permutations(range(80, 100), 2))
    prob_candidates = [[100, i] for i in range(80, 100)]
    error_list_one = []
    error_list_two = []

    # for read_prob_loc, read_prob_info in prob_candidates:
    #     previous_mask_len = 0
    #     tmp_result = []
    #     theory_one = []
    #     theory_two = []
    #     one_flag = True
    #     for i, mask_num in enumerate(mask_num_list):
    #         location_hidden = 0
    #         information_hidden = 0
    #         # write \n
    #         if previous_mask_len != len(mask_num) or i == (len(mask_num_list) - 1):
    #             # theory_result.write("\n")
    #             if one_flag:
    #                 theory_one.append(np.mean(tmp_result))
    #                 if len(theory_one) == len(real_one):
    #                     one_flag = False
    #             else:
    #                 theory_two.append(np.mean(tmp_result))
    #             tmp_result = []
    #
    #         previous_mask_len = len(mask_num)
    #
    #         for num in mask_num:
    #             if num in location_dots:
    #                 location_hidden += 1
    #             elif num in information_dots:
    #                 information_hidden += 1
    #         if location_hidden > 4:
    #             # theory_result.write("0,")
    #             tmp_result.append(0)
    #         elif information_hidden > 7:
    #             # theory_result.write("0,")
    #             tmp_result.append(0)
    #         elif location_hidden == 4 and one_line_check(mask_num, one_line_pattern, location_dots):
    #             # theory_result.write("0,")
    #             tmp_result.append(0)
    #         else:
    #             prob = calc_probability(8 - location_hidden, 4, float(read_prob_loc) * 0.01) * calc_probability(
    #                 15 - information_hidden, 8, float(read_prob_info) * 0.01)
    #             # theory_result.write(str(prob) + ",")
    #             tmp_result.append(prob)
    #
    #     error_list_one.append(np.linalg.norm(np.array(theory_one) - np.array(real_one)))
    #     error_list_two.append(np.linalg.norm(np.array(theory_two) - np.array(real_two)))
    #     print read_prob_loc, read_prob_info
    #
    # print prob_candidates[np.argmin(error_list_one)]
    # print prob_candidates[np.argmin(error_list_two)]

    read_prob_loc = 100
    read_prob_info = 100
    previous_mask_len = 0
    for i, mask_num in enumerate(mask_num_list):
        location_hidden = 0
        information_hidden = 0
        # write \n
        if previous_mask_len != len(mask_num) or i == (len(mask_num_list) - 1):
            theory_result.write("\n")

        previous_mask_len = len(mask_num)

        for num in mask_num:
            if num in location_dots:
                location_hidden += 1
            elif num in information_dots:
                information_hidden += 1
        if location_hidden > 4:
            theory_result.write("0,")

        elif information_hidden > 7:
            theory_result.write("0,")

        elif location_hidden == 4 and one_line_check(mask_num, one_line_pattern, location_dots):
            theory_result.write("0,")
        else:
            prob = calc_probability(8 - location_hidden, 4, float(read_prob_loc) * 0.01) * calc_probability(
                15 - information_hidden, 8, float(read_prob_info) * 0.01)
            theory_result.write(str(prob) + ",")