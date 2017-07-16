#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import cv2
from reedsolo import RSCodec
import sys
import os
import gc
import yaml
import time as tm
import datetime
import threading

path = os.path.join(os.path.dirname(__file__), '../')
sys.path.append(path)
from utils import csv_util, post_util

class TestThread(threading.Thread):

    """docstring for TestThread"""

    def __init__(self, cap):
        super(TestThread, self).__init__()
        self.cap = cap
        self.stop_flag = False
        self.frame = None
        self.ret = None

    def run(self):
        print " === start sub thread (sub class) === "
        while not self.stop_flag:
            self.ret, self.frame = self.cap.read()
            # cv2.imshow("multi_frame", self.frame)
            # cv2.waitKey(1)
        print " === end sub thread (sub class) === "

    def stop(self):
        self.stop_flag = True

def mouse_callback(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        param.append([x, y])


def main():
    # read input args
    if len(sys.argv) != 3:
        print "usage: " + sys.argv[0] + " outer_size fps"
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
    # video_save = False
    skip_mode = True

    # video reader and writer
    cap = cv2.VideoCapture(1)
    cap.set(3, 2592)
    cap.set(4, 1944)

    # csv_file
    csv_every_second = open("./datas/csv/every_second.csv", "w")
    csv_final = open("./datas/csv/final.csv", "w")

    # reed solomon
    rs = RSCodec(14)

    # first select the desk area
    cap.read()
    ret, frame = cap.read()
    print ret
    window_name = "SELECT DESK"
    frame_for_select = cv2.resize(frame, (int(frame.shape[1] * 0.2), int(frame.shape[0] * 0.2)))
    print "Please select left-top and right-down"
    cv2.imshow(window_name, frame_for_select)
    desk_area = []
    cv2.setMouseCallback(window_name, mouse_callback, desk_area)
    cv2.waitKey(0)
    cv2.destroyWindow(window_name)
    desk_area = np.array(desk_area) * 5

    frame_size_0 = frame.shape[0]
    frame_size_1 = frame.shape[1]
    # postit dictionary
    postit_saved = {}
    time = 0.0
    # real time parameters
    newest_key_saved = -1
    projector_resolution = [1024, int(768 * 0.97)]
    desk_area[0][1] = desk_area[0][1] + int((desk_area[1][1] - desk_area[0][1]) * 0.03)

    # reset naruhodo.csv
    try:
        naruhodo_csv = open("./datas/csv/naruhodo.csv", "w")
        naruhodo_csv.close()
    except:
        pass

    th_cl = TestThread(cap)
    th_cl.start()

    while (1):

        # read frame
        print "progress: " + str(int(time / fps) / 60) + ":" + str((time / fps) % 60)
        # ret, frame = cap.read()

        ret = th_cl.ret
        if not ret:
            continue
        frame = th_cl.frame

        cv2.imshow("current", frame)
        cv2.waitKey(1)

        if ret == False:
            break

        # extract only desk area
        frame = frame[desk_area[0][1]:desk_area[1][1], desk_area[0][0]:desk_area[1][0]]
        start_time = tm.time()
        # get postit
        getPostits = post_util.getPostits(frame, outer_size)
        # postit_image = getPostits.postit_image
        # postit_image_analyzing = getPostits.postit_image_analyzing
        postit_points = getPostits.postit_points

        # add buffer
        for i in range(0, len(postit_points)):
            for j in range(0, len(postit_points[i])):
                postit_points[i][j] += desk_area[0]

        # read postit's id and save
        postit_ids = []
        bit_array_list = []
        for i in range(0, len(postit_points)):
            # postit_image_analyzing = cv2.imread("./postit_tmp_analyzing/" + str(i) + ".jpg")
            postit_image_analyzing = np.load("./tmp_datas/postit_tmp_analyzing/" + str(i) + ".npy")
            bit_array = post_util.readDots(postit_image_analyzing).bit_array
            bit_array_list.append(bit_array)
            result_num = -1
            try:
                result_num = rs.decode(bit_array)[0]
            except:
                result_num = -1
            postit_ids.append(result_num)
            # save postit image
            if result_num != -1:
                # already exist
                if postit_saved.has_key(result_num):
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
                                                "first_time": datetime.datetime.today(), "last_time": time / fps,
                                                "move": [],
                                                "rotate": [], "naruhodo": 0}
                    postit_image_for_save = cv2.imread("./tmp_datas/postit_tmp/" + str(i) + ".jpg")
                    cv2.imwrite("./datas/postit_saved/" + str(result_num) + ".jpg", postit_image_for_save)

        # delete old postit(long time no see)
        for id, val in postit_saved.items():
            if (time / fps - val["last_time"]) > time_thre:
                postit_saved[id]["points"] = [[-5, 0], [0, 0], [0, -5], [-5, -5]]

        # write csv
        csv_util.write_every_second(postit_saved, csv_every_second)
        # memory save
        del getPostits
        gc.collect()

        # find newest postit
        newest_key = -1
        newest_time = -1
        for key in postit_saved:
            if postit_saved[key]["first_time"].hour * 60 * 60 + postit_saved[key]["first_time"].minute * 60 + \
                    postit_saved[key]["first_time"].second > newest_time:
                newest_key = key
                newest_time = postit_saved[key]["first_time"].hour * 60 * 60 + postit_saved[key][
                                                                                   "first_time"].minute * 60 + \
                              postit_saved[key]["first_time"].second

        if newest_key != newest_key_saved:
            newest_key_saved = newest_key
            try:
                naruhodo_csv = open("./datas/csv/naruhodo.csv", "w")
                naruhodo_csv.close()
            except:
                pass
        # add naruhodo
        try:
            naruhodo_csv = open("./datas/csv/naruhodo.csv", "r")
            naruhodo_count = len(naruhodo_csv.readlines()) / 2
            naruhodo_csv.close()
            if newest_key != -1:
                postit_saved[newest_key]["naruhodo"] = naruhodo_count
        except:
            pass

        # draw information
        brightness = 10
        down_scale_x = 1.0 * float(projector_resolution[0]) / (desk_area[1][0] - desk_area[0][0])
        down_scale_y = 0.97 * float(projector_resolution[1]) / (desk_area[1][1] - desk_area[0][1])
        x_buffer = 20
        y_buffer = 30

        projection_img = np.uint8(
            [[[brightness, brightness, brightness] for i in range(projector_resolution[0])] for j in
             range(projector_resolution[1])])

        for key in postit_saved:
            caliblated_points = []
            for each_point in postit_saved[key]["points"]:
                caliblated_points.append(np.array([int((each_point[0] - desk_area[0][0]) * down_scale_x) - x_buffer,
                                                   int((each_point[1] - desk_area[0][1]) * down_scale_y) - y_buffer]))
            buff_ratio = 0.1
            caliblated_points[0] += ((caliblated_points[1] - caliblated_points[2]) + (
            caliblated_points[3] - caliblated_points[2])) * buff_ratio
            caliblated_points[1] += ((caliblated_points[0] - caliblated_points[3]) + (
            caliblated_points[2] - caliblated_points[3])) * buff_ratio
            caliblated_points[2] += ((caliblated_points[1] - caliblated_points[0]) + (
            caliblated_points[3] - caliblated_points[0])) * buff_ratio
            caliblated_points[3] += ((caliblated_points[0] - caliblated_points[1]) + (
            caliblated_points[2] - caliblated_points[1])) * buff_ratio

            cv2.drawContours(projection_img,
                             [np.array(caliblated_points)], 0,
                             (0, 200, 243), 5)
            center_point = np.mean(caliblated_points, axis=0)
            # cv2.circle(projection_img, (int((np.mean(postit_saved[key]["points"], axis=0)[0] - desk_area[0][0]) * down_scale_x), int((np.mean(postit_saved[key]["points"], axis=0)[1] - desk_area[0][1]) * down_scale_y)), 100, (0, 0, 200), 5)
            cv2.putText(projection_img, str(postit_saved[key]["naruhodo"]), (
                int(center_point[0] - 20),
                int(center_point[1]) + 20), cv2.FONT_HERSHEY_PLAIN, 4.0,
                        (18, 0, 230), 5)
            d = postit_saved[key]["first_time"]

            cv2.putText(projection_img, str(d.hour) + ":" + str(d.minute) + ":" + str(d.second), (
                int(center_point[0] - 20),
                int(center_point[1] + 100)), cv2.FONT_HERSHEY_PLAIN, 1.5,
                        (197, 126, 24), 2)
        cv2.imshow("projection", projection_img)
        # key waiting
        key = cv2.waitKey(1)
        if key == 27:
            break

        # add time
        time += 1

        print "time: " + str(tm.time() - start_time)

    # final save
    csv_util.write_final(postit_saved, csv_final)
    th_cl.stop()

if __name__ == "__main__":
    main()
