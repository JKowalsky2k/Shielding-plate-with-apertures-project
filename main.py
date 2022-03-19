import scipy.constants
from random import uniform
from math import log, sqrt
from collections import Counter
from pprint import pprint
import cv2
import numpy as np
import argparse

freq = 1.3e9

wave_length = scipy.constants.c / freq

def find_project_req(data):
    try:
        min_sn = 14.
        data = list(filter(lambda x: x["sn"] >= min_sn, data))
        return max(data, key=lambda x: x["quality"])
    except ValueError:
        print("Any Candidate pass project requirements")
        exit(0)

def find_sn(iterations):
    data = []
    for it in range(iterations):
        print("Iterations: {} of {}".format(it+1, iterations), end="\r")
        object_size = round(uniform(0.000001, wave_length/2), 8)
        separation_distance = round(uniform(wave_length / 10, wave_length), 8)
        B = Board(object_size, separation_distance)
        output = {"board": B, "sn": B.getMinSN(), "object_size": object_size, "separation_distance": separation_distance, "quality": object_size*len(B.objects)}
        data.append(output)
    return data

def display_parms_of_board(board):
    print(f'{"bbox_pos_row [m]":<18}', f'{"bbox_pos_col [m]":<18}', f'{"pos_row [m]":<18}', f'{"pos_col [m]":<18}', f'{"lin_dim [m]":<18}', f'{"sn [dB]":<18}')
    for obj in board.objects:
        obj.display()

def display_parms_of_candidate(candidate):
    print("sn =", candidate["sn"])
    print("number of objects =", len(candidate["board"].objects))
    print("object size =", candidate["object_size"])
    print("separation distance =", candidate["separation_distance"])
    print("quality =", candidate["quality"])

def display_info(info):
    print("\n"+str(info))
    print("-"*len(info))

def compare_candidates(candidate1, candidate2):
    print(f'{"Candidate1":<35}',                                                       f'{"Candidate2":<35}')
    print(f'{"sn = "+str(candidate1["sn"]):<35}',                                      f'{"sn = "+str(candidate2["sn"]):<35}')
    print(f'{"number of objects = "+str(len(candidate1["board"].objects)):<35}',       f'{"number of objects = "+str(len(candidate2["board"].objects)):<35}')
    print(f'{"object size = "+str(candidate1["object_size"]):<35}',                    f'{"object size = "+str(candidate2["object_size"]):<35}')
    print(f'{"separation distance = "+str(candidate1["separation_distance"]):<35}',    f'{"separation distance = "+str(candidate2["separation_distance"]):<35}')
    print(f'{"quality = "+str(candidate1["quality"]):<35}',                            f'{"quality = "+str(candidate2["quality"]):<35}')

def visualize_board(board, filename, do_draw_circle = True):
    scale_factor = 1e3
    padding = 50
    window_size = int(.6*scale_factor)
    img = np.zeros((window_size, window_size, 3), dtype=np.uint8)
 
    green = (0, 255, 0)
    red = (0, 0, 255)
    yellow = (0, 255, 255)
    white = (255, 255, 255)
    blue = (255, 0, 0)

    tile_size = int(board["object_size"]*scale_factor)

    furthest_obj = max([(obj, sqrt((obj.bbox_pos_row)**2+(obj.bbox_pos_col)**2)) for obj in board["board"].objects], key=lambda x:x[1])[0]
    bbox_padding = (int((window_size-(furthest_obj.bbox_pos_row*scale_factor)-tile_size-2*padding)/2), int((window_size-(furthest_obj.bbox_pos_col*scale_factor)-tile_size-2*  padding)/2))

    for object in board["board"].objects:
        top_left_corner = (int(object.bbox_pos_row*scale_factor)+padding+bbox_padding[0], int(object.bbox_pos_col*scale_factor)+padding+bbox_padding[1])
        bottom_right_corner = ((int(object.bbox_pos_row*scale_factor)+tile_size)+padding+bbox_padding[0], (int(object.bbox_pos_col*scale_factor)+tile_size)+padding+bbox_padding[1])
        cv2.rectangle(img, top_left_corner, bottom_right_corner, green, 1)

    cv2.rectangle(img, (padding, padding), (padding+int(.5*scale_factor), padding+int(.5*scale_factor)), red, 1)

    font = cv2.FONT_HERSHEY_DUPLEX
    text_pos = (padding, padding//2)
    fontScale = 0.5
    thickness = 1

    text = "obj_size: {}, num_of_objs: {}, sep_dist: {}".format(board["object_size"], len(board["board"].objects), board["separation_distance"])
    text_size = cv2.getTextSize(text, font, fontScale, thickness)[0][0]
    text_pos = (img.shape[0]//2-text_size//2, padding//2)
    cv2.putText(img, text, text_pos, font, fontScale, white, thickness, cv2.LINE_AA)

    img_circle = np.copy(img)

    if do_draw_circle:  
        circle_center_obj = board["board"].objects[len(board["board"].objects)//2] if len(board["board"].objects)%2 else board["board"].objects[int(len(board["board"].objects)
        //2-sqrt(len(board["board"].objects))//2)]
        circle_center = (padding+int(circle_center_obj.pos_col*scale_factor)+bbox_padding[0], padding+int(circle_center_obj.pos_row*scale_factor)+bbox_padding[1])
        cv2.circle(img_circle, circle_center, int(wave_length*scale_factor//2), yellow, 1)

    title = "Candidate with project requirements"

    cv2.imshow(title, img)
    cv2.imshow(title+" (with circle)", img_circle)

    cv2.imwrite(f'{str(filename)+"_with_circle.png"}', img_circle)
    cv2.imwrite(f'{str(filename)+".png"}', img)

def automate_symulation():
    iterations = [100, 1000, 10000, 100000, 1000000]

    for it in iterations:
        display_info("New dataset")
        data = find_sn(it)
        candidate = max(data, key=lambda d:d["sn"])
        candidate_req = find_project_req(data)
        
        display_info("Project candidate")
        display_parms_of_candidate(candidate_req)

        if args.debug:
            display_parms_of_board(candidate_req["board"])

        display_info("Comparsion of two candidates")
        compare_candidates(candidate, candidate_req)
        
        if  args.visualize:
            visualize_board(candidate_req, it)


class Felling:
    def __init__(self, bbox_pos_row, bbox_pos_col, lin_dim) -> None:
        self.linear_dimension = lin_dim
        self.bbox_pos_row = bbox_pos_row
        self.bbox_pos_col = bbox_pos_col
        self.pos_row = self.bbox_pos_row + self.linear_dimension / 2
        self.pos_col = self.bbox_pos_col + self.linear_dimension / 2
        self.sn = 0.
    
    def display(self) -> None:
        print(f"{self.bbox_pos_row:<18.3}", f"{self.bbox_pos_col:<18.3}", f"{self.pos_row:<18.3}", f"{self.pos_col:<18.3}", f"{self.linear_dimension:<18.3}", f"{self.sn:<18.3}")

class Board:
    def __init__(self, object_size, separation_distance=wave_length / 2) -> None:
        self.objects = []
        self.size = .5
        self.placeObjectOnBoard(object_size, separation_distance)
        self.calcSN()

    def getNeigbours(self, pos_row : float, pos_col : float) -> list:
        return [obj for obj in self.objects if sqrt((pos_row - obj.pos_row)**2+(pos_col - obj.pos_col)**2) <= wave_length / 2]

    def SN(self, pos_row : float, pos_col : float, lin_dim : float) -> float:
        sn = 20 * log( wave_length / (2*lin_dim), 10 )
        # uzwgledniamy dziure jak sama siebie bo wtedy n != 0 a musi takie byc bo log
        correcion = -20 * log( sqrt(len(self.getNeigbours(pos_row, pos_col))), 10 )
        return sn+correcion

    def placeObjectOnBoard(self, object_size, separation_distance) -> None:
        can_place_obj_in_row = True
        can_place_obj_in_col = True
        next_pos_in_row = 0.
        next_pos_in_col = 0.

        while (can_place_obj_in_row):
            while (can_place_obj_in_col):
                if next_pos_in_col+object_size+separation_distance <= self.size:
                    self.objects.append(Felling(next_pos_in_row, next_pos_in_col, object_size))
                    next_pos_in_col = next_pos_in_col+object_size+separation_distance
                elif next_pos_in_col+object_size <= self.size:
                    self.objects.append(Felling(next_pos_in_row, next_pos_in_col, object_size))
                    next_pos_in_col = next_pos_in_col+object_size
                    can_place_obj_in_col = False
                else:
                    can_place_obj_in_col = False 

            if next_pos_in_row+object_size+separation_distance <= self.size:
                next_pos_in_row = next_pos_in_row+object_size+separation_distance
            elif next_pos_in_row+object_size <= self.size:
                next_pos_in_row = next_pos_in_row+object_size
                can_place_obj_in_row = False
            else:
                can_place_obj_in_row = False
            
            next_pos_in_col = 0.
            can_place_obj_in_col = True

        self.objects = list(filter(lambda x : x.bbox_pos_row+object_size <= self.size, self.objects))

    def calcSN(self):
        for obj in self.objects:
            obj.sn = self.SN(obj.pos_row, obj.pos_col, obj.linear_dimension)
    
    def getMinSN(self):
        return min([obj.sn for obj in self.objects])

    def getMaxSN(self):
        return max([obj.sn for obj in self.objects])


parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-i', '--iterations', type=int,   default=1,      help='Number of interations')
parser.add_argument('-v', '--visualize',  action="store_true", help='Visualize generated board')
parser.add_argument('-d', '--debug',      action="store_true",  help='debug mode')
parser.add_argument('-a', '--auto',       action="store_true",  help='auto mode')
args = parser.parse_args()

print(args)
if args.auto:
    automate_symulation()
else:
    data = find_sn(args.iterations)

    if args.debug:
        display_info("Dictionary of sn values and their corresponding frequency of accurances")
        pprint(Counter([obj["sn"] for obj in data]))

    candidate = max(data, key=lambda d:d["sn"])

    if args.debug:
        display_info("Best candidate (without project requirements)")
        display_parms_of_candidate(candidate)
        
        info = "\nParameters of each object on board"
        print(info)
        display_parms_of_board(candidate["board"])

    candidate_req = find_project_req(data)

    display_info("Project candidate")
    display_parms_of_candidate(candidate_req)

    if args.debug:
        display_parms_of_board(candidate_req["board"])

    display_info("Comparsion of two candidates")
    compare_candidates(candidate, candidate_req)

    if  args.visualize:
        visualize_board(candidate_req, args.iterations)