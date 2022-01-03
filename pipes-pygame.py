# -*- coding: utf-8 -*-
"""
Created on Mon Dec 20 16:23:51 2021

@author: Henrique Caridade

Pygame implementation of the game pipes.
https://www.puzzle-pipes.com
"""

import pygame
import numpy as np
from time import perf_counter

def main():
    pygame.init()
    
    # --- Nodes Management --- #
    # Node Type:
    # "Receiving_Node / One_Way" -> 0
    # "Straight" -> 1
    # "Two_Way" -> 2
    # "Three_Way" -> 3
    # "Four_Way" -> 4
    #
    # Node Rotation:
    # 0º -> 0
    # 90º -> 1
    # 180º -> 2
    # 270º -> 3
    
    POS = ((0, -1), (1, 0), (0, 1), (-1, 0))
    NODE_ACCESS = ((), (2,), (1,), (1, 2), (1, 2, 3))
    INVERSE_NODE_ACCESS = (((1,0,0,0), (0,1,0,0), (0,0,1,0), (0,0,0,1)),
                           ((1,0,1,0), (0,1,0,1)),
                           ((1,1,0,0), (0,1,1,0), (0,0,1,1), (1,0,0,1)),
                           ((1,1,1,0), (0,1,1,1), (1,0,1,1), (1,1,0,1)),
                           ((1,1,1,1),))
    
    class BlankNode:
        def __init__(self, pos: tuple[int]):
            self.pos = pos
            self.rot = 0
            self.type = 0
            self.with_water = False
            self.up = False
            self.down = False
            self.right = False
            self.left = False
    
    # --- Helper Grid Fuctions --- #
    def clear_water(mat: list[list]):
        for _ in mat:
            for i in _:
                i.with_water = False
                i.update_image()
        aux = len(mat) // 2
        mat[aux][aux].with_water = True
        mat[aux][aux].update_image()
    
    def clear_checks(mat: list[list]):
        for _ in mat:
            for i in _:
                i.checked = False
    
    def everything_is_connected(mat: list[list]) -> bool:
        check_connection(mat)
        for _ in mat:
            for i in _:
                if not i.with_water:
                    return False
        return True
    
    def how_many_are_connected(mat: list[list]) -> int:
        check_connection(mat)
        aux = 0
        for _ in mat:
            for i in _:
                if i.with_water:
                    aux += 1
        return aux
    
    def loops_exist(mat: list[list], edges: list) -> bool:
        before = how_many_are_connected(mat)
        for i in edges:
            edge_aux = i.split("-")
            edge = ((int(edge_aux[0]), int(edge_aux[1])), (int(edge_aux[2]), int(edge_aux[3])))
            pos1, pos2 = edge
            node1 = mat[pos1[1]][pos1[0]]
            node2 = mat[pos2[1]][pos2[0]]
            direction = (pos1[0] - pos2[0], pos1[1] - pos2[1])
            prev_nodes = (node1.down, node1.right, node2.up, node2.left)
            if direction == (0, -1):
                node1.down = False
                node2.up = False
            elif direction == (-1, 0):
                node1.right = False
                node2.left = False
            if before == how_many_are_connected(mat):
                node1.down, node1.right, node2.up, node2.left = prev_nodes
                return True
            node1.down, node1.right, node2.up, node2.left = prev_nodes
        check_connection(mat)
        return False
    
    def check_victory(mat: list[list]):
        for _ in mat:
            for i in _:
                if not i.with_water:
                    return False
        return True
    
    class Node:
        def __init__(self, pos: tuple[int], rot: int, n_type: int):
            self.pos = pos
            self.rot = rot 
            self.type = n_type
            self.with_water = self.type >= 5
            self.checked = False
            self.image = image_getter(self.type, self.with_water, images_resized)
            self.update_rot()
        
        def copy(self):
            return Node(self.pos, self.rot, self.type)
        
        def update_rot(self):
            aux1 = [True]
            aux2 = list(NODE_ACCESS[self.type % 5])
            for i in range(1, 4):
                if aux2:
                    if i == aux2[0]:
                        aux1.append(True)
                        del aux2[0]
                    else:
                        aux1.append(False)
                else:
                    aux1.append(False)
            aux1 = aux1[4 - self.rot:] + aux1[:4 - self.rot]
            self.up, self.right, self.down, self.left = aux1
            
        def update_image(self):
            self.image = image_getter(self.type, self.with_water, images_resized)
        
        def click(self, mat: list[list], clockwise: bool):
            if clockwise:
                self.up, self.right, self.down, self.left = self.left, self.up, self.right, self.down
                self.rot = (self.rot + 1) % 4
            else:
                self.up, self.right, self.down, self.left = self.right, self.down, self.left, self.up
                self.rot = (self.rot - 1) % 4
            edges = check_connection(mat)
            return edges, check_victory(mat)
            
        def def_surrounding_nodes(self, mat: list[list]):
            aux = []
            for i in POS:
                pos = (self.pos[0] + i[0], self.pos[1] + i[1])
                if in_canvas_matrix(pos, mat):
                    aux.append(mat[pos[1]][pos[0]])
                else:
                    aux.append(BlankNode(pos))
            self.node_up, self.node_right, self.node_down, self.node_left = aux
        
        def def_type_rot_image(self):
            aux = (int(self.up), int(self.right), int(self.down), int(self.left))
            for tp, _ in enumerate(INVERSE_NODE_ACCESS):
                for rot, i in enumerate(_):
                    if aux == i: 
                        if self.type < 5:
                            self.type = tp
                        else:
                            self.type = tp + 5
                        self.rot = rot
                        self.update_image()
                        return
        
        def check_connection_helper(self, mat: list[list]) -> list:
            self.checked = True
            # Conections
            connections = [self.up and self.node_up.down,
                           self.right and self.node_right.left,
                           self.down and self.node_down.up,
                           self.left and self.node_left.right]
            water_connections = [connections[0] and self.node_up.with_water,
                                 connections[1] and self.node_right.with_water,
                                 connections[2] and self.node_down.with_water,
                                 connections[3] and self.node_left.with_water]
            edges = []
            for i, con in enumerate(water_connections):
                if con:
                    if i == 0:
                        edges.append(f"{self.node_up.pos[0]}-{self.node_up.pos[1]}-{self.pos[0]}-{self.pos[1]}")
                    elif i == 1:
                        edges.append(f"{self.pos[0]}-{self.pos[1]}-{self.node_right.pos[0]}-{self.node_right.pos[1]}")
                    elif i == 2:
                        edges.append(f"{self.pos[0]}-{self.pos[1]}-{self.node_down.pos[0]}-{self.node_down.pos[1]}")
                    elif i == 3:
                        edges.append(f"{self.node_left.pos[0]}-{self.node_left.pos[1]}-{self.pos[0]}-{self.pos[1]}")
            if self.type < 5:
                self.with_water = False
                if any(water_connections):
                    self.with_water = True
            if self.with_water:
                if connections[0] and not self.node_up.checked:
                    edges.extend(self.node_up.check_connection_helper(mat))
                if connections[1] and not self.node_right.checked:
                    edges.extend(self.node_right.check_connection_helper(mat))
                if connections[2] and not self.node_down.checked:
                    edges.extend(self.node_down.check_connection_helper(mat))
                if connections[3] and not self.node_left.checked:
                    edges.extend(self.node_left.check_connection_helper(mat))
            self.image = image_getter(self.type, self.with_water, images_resized)
            return edges
                
    def check_connection(mat: list[list]) -> list:
        clear_water(mat)
        x = len(mat) // 2
        edges = mat[x][x].check_connection_helper(mat)
        clear_checks(mat)
        return edges
    
    # --- Image Management Functions --- #
    def get_images() -> dict:
        start = ["Receiver_Node", "Straight_Tube", "Two_Way_Tube", "Three_Way_Tube", "Four_Way_Tube"]
        end = ["Without_Water", "With_Water"]
        aux_dict = {}
        for st in start:
            for ed in end:
                aux_dict[st] = aux_dict.get(st, ()) + (pygame.image.load("Images\\" + st + "_" + ed + ".png"),)
        start = ["One_Way", "Straight", "Two_Way", "Three_Way", "Four_Way"]
        for st in start:
            aux_dict[st + "_Source_Node"] = pygame.image.load("Images\\" + st + "_Source_Node.png")
        return aux_dict
    
    def image_getter(n: int, water: bool, images: dict):
        # 15 images
        # 10 pieces
        # 5 variants
        n %= 10
        
        start1 = ["Receiver_Node", "Straight_Tube", "Two_Way_Tube", "Three_Way_Tube", "Four_Way_Tube"]
        start2 = ["One_Way", "Straight", "Two_Way", "Three_Way", "Four_Way"]
        if n < 5:
            image_i = n
            image_j = int(water)
            image = images[start1[image_i]][image_j]
        else:
            image_i = n - 5
            image = images[start2[image_i] + "_Source_Node"]
        return image
    
    def resize_images(side: int, images: dict):
        image_size = (side, side)
        start = ["Receiver_Node", "Straight_Tube", "Two_Way_Tube", "Three_Way_Tube", "Four_Way_Tube"]
        # end = ["Without_Water", "With_Water"]
        aux_dict = {}
        for st in start:
            aux_dict[st] = (pygame.transform.scale(images[st][0], image_size),
                            pygame.transform.scale(images[st][1], image_size))
        start = ["One_Way", "Straight", "Two_Way", "Three_Way", "Four_Way"]
        for st in start:
            aux_dict[st + "_Source_Node"] = pygame.transform.scale(images[st + "_Source_Node"], image_size)
        return aux_dict
    
    # --- Grid Functions --- #
    def scrabble_matrix(mat: list[list]):
        for _ in mat:
            for i in _:
                i.rot = np.random.randint(4)
                i.update_rot()
    
    def get_tubulation(side_length: int) -> list[list]:
        center_node_pos = (side_length // 2, side_length // 2)
        matrix = []
        for row in range(side_length):
            aux = []
            for col in range(side_length):
                if (row, col) != center_node_pos:
                    tp = 4
                    rot = 0
                    if row == 0 or row == side_length - 1:
                        tp -= 1
                    if col == 0 or col == side_length - 1:
                        tp -= 1
                    if row == 0 and 0 <= col < side_length - 1:
                        rot = 1
                    elif col == side_length - 1 and 0 <= row < side_length - 1:
                        rot = 2
                    elif row == side_length - 1 and 0 < col < side_length:
                        rot = 3
                    aux.append(Node((col, row), rot, tp))
                else: 
                    aux.append(Node(center_node_pos, 0, 9))
            matrix.append(aux)
        for _ in matrix:
            for i in _:
                i.def_surrounding_nodes(matrix)
        horizontal_edges = [f"{i}-{j}-{i}-{j + 1}" for i in range(side_length) for j in range(side_length - 1)]
        vertical_edges = [f"{i}-{j}-{i + 1}-{j}" for i in range(side_length - 1) for j in range(side_length)]
        edges = horizontal_edges + vertical_edges
        exited = False
        while loops_exist(matrix, edges):
            while everything_is_connected(matrix):
                edge_aux1 = np.random.choice(edges)
                edge_aux = edge_aux1.split("-")
                edge = ((int(edge_aux[0]), int(edge_aux[1])), (int(edge_aux[2]), int(edge_aux[3])))
                pos1, pos2 = edge
                direction = (pos1[0] - pos2[0], pos1[1] - pos2[1])
                node1 = matrix[pos1[1]][pos1[0]]
                node2 = matrix[pos2[1]][pos2[0]]
                if direction == (0, -1):
                    node1.down = False
                    node2.up = False
                elif direction == (-1, 0):
                    node1.right = False
                    node2.left = False
                edges.remove(edge_aux1)
                exited = True
            if exited:
                exited = False
                if direction == (0, -1):
                    node1.down = True
                    node2.up = True
                elif direction == (-1, 0):
                    node1.right = True
                    node2.left = True
        for _ in matrix:
            for i in _:
                i.def_type_rot_image()
        return matrix
    
    # --- Helper Functions --- #
    def input_is_valid(given_input: str, bounds: tuple[int]):
        if given_input:
            num = int(given_input)
            if bounds[0] <= num <= bounds[1]:
                return "Clear"
            else:
                return "OutOfRange"
        return "Length"
    
    def in_canvas_matrix(pos: tuple[int], mat: list[list]):
        mat_len = len(mat)
        return 0 <= pos[0] < mat_len and 0 <= pos[1] < mat_len
    
    def in_canvas_pixels(ipt: tuple[int]):
        left_bounds = grid_origin[0]
        right_bounds = grid_origin[0] + grid_size
        up_bounds = grid_origin[1]
        down_bounds = grid_origin[1] + grid_size
        return left_bounds <= ipt[0] < right_bounds and up_bounds <= ipt[1] < down_bounds
    
    def time_formatter(time: float):
        minutes = str(int(time / 60))
        seconds = str(int(time % 60))
        return minutes.zfill(2) + ":" + seconds.zfill(2)
        
    # --- Constants & Variables --- #
    SCREEN_SIZE = (1280, 720) # Scalable
    COLORS = {"passive": pygame.Color((102, 102, 102)),
              "active": pygame.Color((99, 182, 230)),
              "white": pygame.Color((255, 255, 255)),
              "background": pygame.Color((64, 64, 64)),
              "timer": pygame.Color((255, 255, 255)), 
              "error": pygame.Color((180, 30, 30)),
              "grid_back": pygame.Color((170, 170, 170)),
              "grid_back_loop": pygame.Color((200, 100, 100)),
              "grid_lines": pygame.Color((220, 220, 220)),
              "victory": pygame.Color((0, 200, 0)),
              "loading": pygame.Color((200, 200, 200))}
    BACKGROUND_COLOR = COLORS["background"]
    
    grid_size = min(SCREEN_SIZE)
    if SCREEN_SIZE[0] <= SCREEN_SIZE[1]:
        grid_origin = (0, (SCREEN_SIZE[1] - SCREEN_SIZE[0]) // 2)
    else:
        grid_origin = ((SCREEN_SIZE[0] - SCREEN_SIZE[1]) // 2, 0)
    IMAGES = get_images()
    images_side_length = 360
    grid_size_BOUNDS = (4, 25)
    
    screen = pygame.display.set_mode(SCREEN_SIZE, pygame.SRCALPHA)
    pygame.display.set_caption("Pygame Pipes")
    
    # Starting Screen Variables
    TEXTBOX_SIZE = (SCREEN_SIZE[0] // 8, SCREEN_SIZE[1] // 8)
    TEXTBOX_POS = (SCREEN_SIZE[0] // 2 - TEXTBOX_SIZE[0] // 2, SCREEN_SIZE[1] // 2)
    TEXTBOX_PADDING = TEXTBOX_SIZE[1] // 10
    textbox_rect = pygame.Rect(TEXTBOX_POS, TEXTBOX_SIZE)
    textbox_color = COLORS["passive"]
    textbox_text = ""
    textbox_text_color = COLORS["white"]
    textbox_font = pygame.font.Font(None, TEXTBOX_SIZE[1])
    textbox_is_active = False
    
    title_text = "PIPES"
    title_color = COLORS["passive"]
    title_font = pygame.font.Font(None, SCREEN_SIZE[1] // 3)
    
    ERRORS = {"OutOfRange": "[ERROR] The number you typed isn't in the permited range.",
              "Length": "[ERROR] You gave no input.",
              "Clear": ""}
    ERROR_MARGIN = SCREEN_SIZE[1] // 120
    error_text = ERRORS["Clear"]
    error_color = COLORS["error"]
    error_font = pygame.font.Font(None, SCREEN_SIZE[1] // 16)
    
    INFO_MARGIN = SCREEN_SIZE[1] // 120
    info_text = f"Size must be between {grid_size_BOUNDS[0]} and {grid_size_BOUNDS[1]}."
    info_color = COLORS["passive"]
    info_font = pygame.font.Font(None, SCREEN_SIZE[1] // 12)
    
    credits_text =  "Made by Henrique Caridade"
    credits_color = COLORS["passive"]
    credits_font = pygame.font.Font(None, SCREEN_SIZE[1] // 8)
    
    # Game Screen Variables
    victory_text = ""
    victory_color = COLORS["victory"]
    victory_font = pygame.font.Font(None, SCREEN_SIZE[1] // 3)
    
    timer_text = "00:00"
    timer_color = COLORS["timer"]
    timer_font = pygame.font.Font(None, SCREEN_SIZE[1] // 2)
    
    victory_timer_text = ""
    victory_timer_color = COLORS["victory"]
    victory_timer_font = pygame.font.Font(None, SCREEN_SIZE[1] // 6)
    
    loading_text = "Loading..."
    loading_color = COLORS["loading"]
    loading_font = pygame.font.Font(None, SCREEN_SIZE[1] // 4)
    
    grid_back_alpha = 150
    antialias = True
    
    # Other Variables
    curr_screen = "starting"
    running = True
    victory = False
    
    # --- Game Loop --- #
    while running:
        # --- Input Management --- #
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
                continue
            if curr_screen == "starting":
                # --- Starting Screen Inputs --- #
                if ev.type == pygame.MOUSEBUTTONDOWN:
                    if ev.button == 1:
                        if textbox_rect.collidepoint(ev.pos):
                            textbox_is_active = True
                        else:
                            textbox_is_active = False
                if ev.type == pygame.KEYDOWN:
                    if textbox_is_active:
                        if ev.key == pygame.K_BACKSPACE:
                            textbox_text = textbox_text[:-1]
                        elif ev.key == pygame.K_RETURN:
                            input_check = input_is_valid(textbox_text, grid_size_BOUNDS)
                            if input_check == "Clear":
                                ipt = int(textbox_text)
                                curr_screen = "game"
                                error_text = ERRORS["Clear"]
                                
                                images_side_length = grid_size // ipt
                                difference = grid_size % ipt
                                grid_size -= difference
                                grid_origin = (grid_origin[0] + difference // 2, grid_origin[1] + difference // 2)
                                grid_back_rect_screen = pygame.Surface((grid_size, grid_size))
                                grid_back_rect_screen.set_alpha(grid_back_alpha)
                                curr_back_color = COLORS["grid_back"]
                                
                                images_resized = resize_images(images_side_length, IMAGES)
                                
                                # Loading Text
                                loading_surface = loading_font.render(loading_text, antialias, loading_color)
                                screen.blit(loading_surface, ((SCREEN_SIZE[0] - loading_surface.get_width()) // 2,
                                                              (SCREEN_SIZE[1] - loading_surface.get_height()) // 16 * 13))
                                pygame.display.flip()
                                
                                game_matrix = get_tubulation(ipt)
                                
                                scrabble_matrix(game_matrix)
                                check_connection(game_matrix)
                                start_time = perf_counter()
                            else:
                                error_text = ERRORS[input_check]
                                textbox_text = ""
                        else:
                            char = ev.unicode
                            if char.isnumeric():
                                textbox_text += char
            elif curr_screen == "game":
                # --- Game Screen Inputs --- #
                if not victory:
                    if ev.type == pygame.MOUSEBUTTONDOWN:
                        if ev.button in (1, 3):
                            mouse_click = ev.pos
                            if in_canvas_pixels(mouse_click):
                                clockwise = ev.button == 1
                                mat_coords = ((mouse_click[0] - grid_origin[0]) // images_side_length,
                                              (mouse_click[1] - grid_origin[1]) // images_side_length,)
                                curr_node = game_matrix[mat_coords[1]][mat_coords[0]]
                                edges, victory = curr_node.click(game_matrix, clockwise)
                                if loops_exist(game_matrix, edges):
                                    curr_back_color = COLORS["grid_back_loop"]
                                else:
                                    curr_back_color = COLORS["grid_back"]
                                if victory:
                                    victory_text = "VICTORY"
                                    victory_timer_text = time_formatter(perf_counter() - start_time)
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_RETURN:
                        curr_screen = "starting"
                        victory = False
                        victory_text = ""
                        victory_timer_text = ""
                        timer_text = "00:00"
                        grid_size = min(SCREEN_SIZE)
                        if SCREEN_SIZE[0] <= SCREEN_SIZE[1]:
                            grid_origin = (0, (SCREEN_SIZE[1] - SCREEN_SIZE[0]) // 2)
                        else:
                            grid_origin = ((SCREEN_SIZE[0] - SCREEN_SIZE[1]) // 2, 0)
                    
        # --- Display Screen --- #
        screen.fill(BACKGROUND_COLOR)
        
        if curr_screen == "starting":
            # --- Starting Screen --- #
            
            # Text Box Color
            if textbox_is_active:
                textbox_color = COLORS["active"]
            else:
                textbox_color = COLORS["passive"]
            
            # Title
            title_surface = title_font.render(title_text, antialias, title_color)
            screen.blit(title_surface, ((SCREEN_SIZE[0] - title_surface.get_width()) // 2,
                                        SCREEN_SIZE[1] // 8))
            
            # Text Box
            pygame.draw.rect(screen, textbox_color, textbox_rect)
            textbox_surface = textbox_font.render("Size: " + textbox_text, antialias, textbox_text_color)
            textbox_rect.w = max(TEXTBOX_SIZE[0], textbox_surface.get_width() + TEXTBOX_PADDING * 2)
            textbox_rect.left = (SCREEN_SIZE[0] - textbox_rect.width) // 2
            textbox_surface_pos = (textbox_rect.left + TEXTBOX_PADDING, textbox_rect.bottom - textbox_surface.get_height() - TEXTBOX_PADDING)
            screen.blit(textbox_surface, textbox_surface_pos)
            
            # Info Text
            info_surface = info_font.render(info_text, antialias, info_color)
            screen.blit(info_surface, ((SCREEN_SIZE [0] - info_surface.get_width()) // 2,
                                        textbox_rect.top - info_surface.get_height() - INFO_MARGIN))
            
            # Error Message
            error_surface = error_font.render(error_text, antialias, error_color)
            screen.blit(error_surface, ((SCREEN_SIZE [0] - error_surface.get_width()) // 2,
                                        textbox_rect.bottom + ERROR_MARGIN))
            
            # Credits
            credits_surface = credits_font.render(credits_text, antialias, credits_color)
            screen.blit(credits_surface, ((SCREEN_SIZE[0] - credits_surface.get_width()) // 2,
                                        SCREEN_SIZE[1] // 8 * 7))
            
        elif curr_screen == "game":
            # --- Game Screen --- #
            if not victory:
                total_time = perf_counter() - start_time
                timer_text = time_formatter(total_time)
                
            # Timer Behind Grid
            timer_surface = timer_font.render(timer_text, antialias, timer_color)
            screen.blit(timer_surface, ((SCREEN_SIZE[0] - timer_surface.get_width()) // 2,
                                            (SCREEN_SIZE[1] - timer_surface.get_height()) // 2))
            
            # Grid Background
            grid_back_rect_screen.fill(curr_back_color)
            screen.blit(grid_back_rect_screen, grid_origin)
            
            # Grid
            for x in range(grid_origin[0], grid_origin[0] + grid_size + 1, images_side_length):
                pygame.draw.line(screen, COLORS["grid_lines"], (x, grid_origin[1]), (x, grid_origin[1] + grid_size))
            for y in range(grid_origin[1], grid_origin[1] + grid_size + 1, images_side_length):
                pygame.draw.line(screen, COLORS["grid_lines"], (grid_origin[0], y), (grid_origin[0] + grid_size, y))
            
            # Display Game Matrix
            for row in game_matrix:
                for item in row:
                    image = item.image
                    image = pygame.transform.rotate(image, - 90 * item.rot)
                    image_pos = (grid_origin[0] + item.pos[0] * images_side_length,
                                 grid_origin[1] + item.pos[1] * images_side_length)
                    screen.blit(image, image_pos)
            
            # Victory Text
            victory_surface = victory_font.render(victory_text, antialias, victory_color)
            screen.blit(victory_surface, ((SCREEN_SIZE[0] - victory_surface.get_width()) // 2,
                                            (SCREEN_SIZE[1] - victory_surface.get_height()) // 2))
            
            # Victory Timer Text
            victory_timer_surface = victory_timer_font.render(victory_timer_text, antialias, victory_timer_color)
            screen.blit(victory_timer_surface, ((SCREEN_SIZE[0] - victory_timer_surface.get_width()) // 2,
                                                (SCREEN_SIZE[1] - victory_timer_surface.get_height()) // 3 * 2))
        
        # Center Check
        # pygame.draw.line(screen, (0, 0, 0), (SCREEN_SIZE[0] // 2, 0), (SCREEN_SIZE[0] // 2, SCREEN_SIZE[1]))
        # pygame.draw.line(screen, (0, 0, 0), (0, SCREEN_SIZE[1] // 2), (SCREEN_SIZE[0], SCREEN_SIZE[1] // 2))
        
        # Refresh Screen
        pygame.display.flip()
    
    pygame.quit()

if __name__ == "__main__":
    main()
