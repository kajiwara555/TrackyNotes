#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gc
import os
import sys

import cv2
import numpy as np
from reedsolo import RSCodec
import yaml

path = os.path.join(os.path.dirname(__file__), '../')
sys.path.append(path)
from utils import csv_util, post_util


def mouse_callback(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        param.append([x, y])

#id using 108-117

def main():
    # read input args
    if len(sys.argv) != 3:
        print("usage: " + sys.argv[0] + " outer_size fps")
        return -1
    outer_size = int(sys.argv[1])
    fps = int(sys.argv[2])
    # delete old postit image
    old_postit_image = os.listdir('./datas/postit_saved/')
    for old_postit in old_postit_image:
        os.remove('./datas/postit_saved/' + old_postit)

    # memory save
    gc.enable()

    # set parameter
    analyse_config = yaml.load(open("./config/analyse_config.yaml", "r"))
    dist_thre = analyse_config["dist_thre"]
    angle_thre = analyse_config["angle_thre"]
    time_thre = analyse_config["time_thre"]
    video_save = False
    skip_mode = True

    # read movie file list
    movie_id = 0
    movie_files = os.listdir('./datas/movie/')
    if len(movie_files) == 0:
        print("no movie")
        return -1
    else:
        print("movie files:")
        for movie_file_each in movie_files:
            print(movie_file_each)

    # # video reader and writer
    # cap = cv2.VideoCapture('./datas/movie/' + movie_files[0])
    # if video_save:
    #     writer = cv2.VideoWriter("./datas/movie/OUT.avi", cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'), fps, (3840, 2160))
    # csv_file
    csv_every_second = open("./datas/csv/every_second.csv", "w")
    csv_final = open("./datas/csv/final.csv", "w")

    # reed solomon
    rs = RSCodec(14)

    # # first select the desk area
    # ret, frame = cap.read()
    # window_name = "SELECT DESK"
    # frame_for_select = cv2.resize(frame, (int(frame.shape[1] * 0.2), int(frame.shape[0] * 0.2)))
    # print "Please select left-top and right-down"
    # cv2.imshow(window_name, frame_for_select)
    # desk_area = []
    # cv2.setMouseCallback(window_name, mouse_callback, desk_area)
    # cv2.waitKey(0)
    # cv2.destroyWindow(window_name)
    # desk_area = np.array(desk_area) * 5
    # # select the mask area
    # window_name = "SELECT left-top, right-top, right-down"
    # print "Please select left-top and right-down"
    # cv2.imshow(window_name, frame[desk_area[0][1]:desk_area[1][1], desk_area[0][0]:desk_area[1][0]])
    # postit_area = []
    # cv2.setMouseCallback(window_name, mouse_callback, postit_area)
    # cv2.waitKey(0)
    # cv2.destroyWindow(window_name)
    # postit_area_width = np.linalg.norm(np.array(postit_area[0]) - np.array(postit_area[1]))
    # postit_area_height = np.linalg.norm(np.array(postit_area[1]) - np.array(postit_area[2]))
    postit_area_width = 424
    postit_area_height = 319

    # result file
    experiment_result = open("./datas/csv/resolution_result.csv", "w")
    # experiment_result.write(str(desk_area) + "\n")

    # set desk by myself
    # desk_area = np.array([[1615, 890], [2110, 1285]])
    for movie_id in range(len(movie_files)):
        for resolution in range(0, 99):
            resolution = float(resolution) * 0.01
            print("pattern:" + str(resolution))
            time = 0
            success_count = 0
            postit_saved = {}
            # cap = cv2.VideoCapture('./datas/movie/' + movie_files[movie_id])

            # read frame
            # print "progress: " + str(time)
            frame = cv2.imread('./datas/movie/' + movie_files[movie_id])
            # frame = cv2.resize(frame, (postit_area_width, postit_area_height), interpolation=cv2.INTER_LINEAR)


            # # extract only desk area
            # frame = frame[desk_area[0][1]:desk_area[1][1], desk_area[0][0]:desk_area[1][0]]

            # change resolution
            frame = cv2.resize(frame,
                               (int(postit_area_width * (1 - resolution)), int(postit_area_height * (1 - resolution))),
                               interpolation=cv2.INTER_CUBIC)
            frame_for_save = np.copy(frame)
            outer_size_resized = outer_size * ((1 - resolution) ** 2)

            # save frame for final
            frame_for_final = np.copy(frame)

            # get postit
            getPostits = post_util.getPostits(frame, outer_size_resized)
            # postit_image_analyzing = getPostits.postit_image_analyzing
            postit_points = getPostits.postit_points
            recognized_location_rectangle = getPostits.recognized_location_rectangle
            recognized_id_rectangle = 0
            # # add buffer
            # for i in range(0, len(postit_points)):
            #     for j in range(0, len(postit_points[i])):
            #         postit_points[i][j] += desk_area[0]

            # read postit's id and save
            postit_ids = []
            bit_array_list = []
            for i in range(0, len(postit_points)):
                # postit_image_analyzing = cv2.imread("./postit_tmp_analyzing/" + str(i) + ".jpg")
                postit_image_analyzing = np.load("./tmp_datas/postit_tmp_analyzing/" + str(i) + ".npy")
                bit_array = post_util.readDots(postit_image_analyzing).bit_array

                bit_array_answer = []
                for num in rs.encode([108 + movie_id]):
                    bit_array_answer.append(num)

                bit_array_list.append(bit_array)
                result_num = -1
                try:
                    result_num = rs.decode(bit_array)[0]
                except:
                    result_num = -1

                # success check
                # if (recognized_location_rectangle == 8) and bit_array_answer == bit_array:
                #     success_count += 1

                for each_bit in zip(bit_array_answer, bit_array):
                    if each_bit[0] == each_bit[1]:
                        recognized_id_rectangle += 1
                success_count += recognized_id_rectangle + recognized_location_rectangle

                postit_ids.append(result_num)
                # save postit image
                if result_num != -1:
                    # already exist
                    if result_num in postit_saved:
                        # judge move and rotate
                        # calc dist
                        dist = np.linalg.norm(
                            np.mean(postit_saved[result_num]["points_saved"], axis=0) - np.mean(postit_points[i],
                                                                                                axis=0))
                        # calc angle(degree)
                        angle_vec_before = np.array(postit_saved[result_num]["points_saved"][0]) - np.array(
                            postit_saved[result_num]["points_saved"][1])
                        angle_vec_after = np.array(postit_points[i][0]) - np.array(postit_points[i][1])
                        vec_cos = np.dot(angle_vec_before, angle_vec_after) / (
                            np.linalg.norm(angle_vec_before) * np.linalg.norm(angle_vec_after))
                        angle = np.arccos(vec_cos) * 180 / np.pi
                        # add information
                        if dist > dist_thre:
                            if len(postit_saved[result_num]["move"]) == 0:
                                postit_saved[result_num]["move"].append(time / fps)
                            elif (time / fps - postit_saved[result_num]["move"][-1]) > 5:
                                postit_saved[result_num]["move"].append(time / fps)
                        elif angle > angle_thre:
                            if len(postit_saved[result_num]["rotate"]) == 0:
                                postit_saved[result_num]["rotate"].append(time / fps)
                            elif (time / fps - postit_saved[result_num]["rotate"][-1]) > 5:
                                postit_saved[result_num]["rotate"].append(time / fps)
                        # renew
                        postit_saved[result_num]["points"] = postit_points[i]
                        postit_saved[result_num]["points_saved"] = postit_points[i]
                        postit_saved[result_num]["last_time"] = time / fps
                    # first appear
                    else:
                        postit_saved[result_num] = {"points": postit_points[i], "points_saved": postit_points[i],
                                                    "first_time": time / fps, "last_time": time / fps, "move": [],
                                                    "rotate": []}
                        postit_image_for_save = cv2.imread("./tmp_datas/postit_tmp/" + str(i) + ".jpg")
                        cv2.imwrite("./datas/postit_saved/" + str(result_num) + ".jpg", postit_image_for_save)

            # delete old postit(long time no see)
            for id, val in list(postit_saved.items()):
                if (time / fps - val["last_time"]) > time_thre:
                    postit_saved[id]["points"] = [[-5, 0], [0, 0], [0, -5], [-5, -5]]

            # write csv
            csv_util.write_every_second(postit_saved, csv_every_second)
            # memory save
            del getPostits
            gc.collect()

            # key waiting
            key = cv2.waitKey(1)
            if key == 27:
                break

            # when drawing dict info
            for key in postit_saved:
                cv2.drawContours(frame_for_final, [np.array(postit_saved[key]["points"]).astype(np.int)], 0,
                                 (0, 0, 220), 2)
                cv2.putText(frame_for_final, str(key), (
                    np.mean(postit_saved[key]["points"], axis=0).astype(np.int)[0] - 40,
                    np.mean(postit_saved[key]["points"], axis=0).astype(np.int)[1]), cv2.FONT_HERSHEY_PLAIN, 5.0,
                            (0, 140, 0), 5)
            show_img_final = cv2.resize(frame_for_final,
                                        (int(frame_for_final.shape[1] * 0.3), int(frame_for_final.shape[0] * 0.3)))
            cv2.imshow("show2", show_img_final)

            # add time
            time += 1

            if time > 23:
                break

            # final save
            csv_util.write_final(postit_saved, csv_final)

            # print success rate
            experiment_result.write(str(int(postit_area_height * (1 - resolution))) + "," + str(
                int(postit_area_width * (1 - resolution))) + "," + str(time) + "," + str(success_count) + "," + str(
                float(success_count) / time) + "\n")
            cv2.imwrite("./datas/postit_saved/frame.jpg", frame_for_save)
            print("-----success result------")
            print("resolution:" + str(int(postit_area_height * (1 - resolution))) + "," + str(
                int(postit_area_width * (1 - resolution))))
            print("success count: " + str(success_count))
            print("id: " + str(recognized_id_rectangle))
            print("loc: " + str(recognized_location_rectangle))
            print("time:" + str(time))
            print("success rate: " + str(float(success_count) / time))


if __name__ == "__main__":
    main()
