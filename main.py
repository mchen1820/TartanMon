import cv2
import pygame
import numpy as np
import mediapipe as mp
import HandTrackingModule as htm
from cvzone.HandTrackingModule import HandDetector
from screens import *
from trainer import *
from player_mon import *
from opponent_mon import *
from text_box import *
from func import *
import app

pygame.init()

# set up camera display
screen_width, screen_height = 900, 600
screen = pygame.display.set_mode((screen_width, screen_height))

# initialize OpenCV camera
cap = cv2.VideoCapture(0)  # use 0 for default webcam
cap.set(cv2.CAP_PROP_FRAME_WIDTH, screen_width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, screen_height)

# get original camera feed dimensions
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
frame = cv2.flip(cap.read()[1], 1)  # read and flip in one line
aspect_ratio = frame_width / frame_height

# define target size for camera feed in Pygame
target_height = screen_height//4   # 1/4 of screen height
target_width = int(target_height * aspect_ratio)  # Maintain aspect ratio

# initialize Hand Detector
detector = HandDetector(detectionCon=0.8, maxHands=2)

# initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2, 
                       min_detection_confidence=0.5)

# define the target sequence of gestures
move_list = ["Fly", "fist_palm","dragonBall","Triangle"]
special_list= ["Catch","Swipe","Throw","Exit_sequence"]

# initialize variables for sequence recognition
sequence_buffer = []  # stores detected gestures
sequence_index = 0    # tracks progress in target sequence
buffer_size = 30      # buffer size

# throw calculation
zL = []
zR = []
left_is_throwing = False
right_is_throwing = False

# reverse throw calculation
zL_rev = []
zR_rev=[]
left_is_catching = False
right_is_catching = False

# swipe calculation
LHX = []
RHX = []
right_is_swiping = False
left_is_swiping = False

sequence_complete = False
just_caught = True

def display_mouse(coordinates, color):
    x,y = coordinates
    pygame.draw.circle(screen,color,(x,y),10,2)

pygame.mouse.set_pos(app.mouseX, app.mouseY)
wait = 5

while app.running:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            app.running = False 
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # moves to info guide if start button is clicked
            if app.in_start and pressedStart((app.mouseX, app.mouseY)):
                toGuide()
                app.mousePressed = False
            # moves to selection screen if got it button is clicked
            elif app.in_guide and pressedGotIt((app.mouseX, app.mouseY)):
                toSelect()
                app.mousePressed = False
            # selects Tartanmon if image is clicked
            elif app.in_select:
                if hoverBulb((app.mouseX, app.mouseY)): # choosing Bulbasaur
                    if not(app.bulbDead):
                        toBattle() # changes screen to battle screen
                        app.trainer = Trainer() # initializes trainer sprite
                        app.pickBulb = True
                        app.pickChar = False
                        app.pickSquirt = False
                        app.curr_pokemon = None
                        app.curr_pokemon_dead = False
                elif hoverChar((app.mouseX, app.mouseY)): # choosing Charmander
                    if not(app.charDead):
                        toBattle()
                        app.trainer = Trainer()
                        app.pickBulb = False
                        app.pickChar = True
                        app.pickSquirt = False
                        app.curr_pokemon = None
                        app.curr_pokemon_dead = False
                elif hoverSquirt((app.mouseX, app.mouseY)): # choosing Squirtle
                    if not(app.squirtDead):
                        toBattle()
                        app.trainer = Trainer()
                        app.pickBulb = False
                        app.pickChar = False
                        app.pickSquirt = True
                        app.curr_pokemon = None
                        app.curr_pokemon_dead = False
                elif hoverReturn((app.mouseX, app.mouseY)): #return page
                        toGuide()
                        app.mousePressed = False
            # restarts game if the player has won or lost
            elif ((app.in_win or app.in_lose) and 
                    (pressedPlayAgain((app.mouseX, app.mouseY)))):
                toStart()
                app.reset()

    app.current_time = pygame.time.get_ticks()

    screen.fill((0,0,0))
    app.canvas.blit(app.bg, (0,0))

    app.mouseX, app.mouseY = pygame.mouse.get_pos()

    # capture frame from OpenCV
    ret, frame = cap.read()
    if not ret:
        break
    
    # detect hands using cvzone
    hands_detected, img = detector.findHands(frame, draw=True)

    # initialize detected gesture
    current_gesture = "None"

    left_hand = None
    right_hand = None

    if hands_detected:
        for hand in hands_detected:
            if hand["type"] == "Left":
                left_hand = hand
            else:
                right_hand = hand
            hand_type = hand["type"]

            # display hand type on screen
            bbox = hand["bbox"]
            cv2.putText(frame, f"{hand_type} Hand", (bbox[0], bbox[1] - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        if len(hands_detected) == 1:
            hand = hands_detected[0]
            isClick, coord = detect_mouse(hand, detector.fingersUp(hand), 
                                          screen_width)
            
            if not isClick:
                app.mousePressed = False
                wait = 5
                withinX = coord[0] >= 0 and coord[0] <= screen_width
                withinY = coord[1] >= 0 and coord[1] <= screen_height
                if (withinX and withinY):
                   app.mouseX = coord[0]
                   app.mouseY = coord[1]
                   pygame.mouse.set_pos((app.mouseX,app.mouseY))
            else:
                wait -= 1
                if wait == 0:
                    app.mousePressed = True
                # moves to info guide if start button is clicked
                if app.in_start and pressedStart((app.mouseX, app.mouseY)):
                    toGuide()
                    app.mousePressed = False
                # moves to selection screen if got it button is clicked
                elif app.in_guide and pressedGotIt((app.mouseX, app.mouseY)):
                    toSelect()
                    app.mousePressed = False
                # selects Tartanmon if image is clicked
                elif app.in_select:
                    if hoverBulb((app.mouseX, app.mouseY)): # choosing Bulbasaur
                        if not(app.bulbDead):
                            toBattle() # changes screen to battle screen
                            app.trainer = Trainer() # initializes trainer sprite
                            app.pickBulb = True
                            app.pickChar = False
                            app.pickSquirt = False
                            app.curr_pokemon = None
                            app.curr_pokemon_dead = False
                    elif hoverChar((app.mouseX, app.mouseY)): # choosing Charmander
                        if not(app.charDead):
                            toBattle()
                            app.trainer = Trainer()
                            app.pickBulb = False
                            app.pickChar = True
                            app.pickSquirt = False
                            app.curr_pokemon = None
                            app.curr_pokemon_dead = False
                    elif hoverSquirt((app.mouseX, app.mouseY)): # choosing Squirtle
                        if not(app.squirtDead):
                            toBattle()
                            app.trainer = Trainer()
                            app.pickBulb = False
                            app.pickChar = False
                            app.pickSquirt = True
                            app.curr_pokemon = None
                            app.curr_pokemon_dead = False
                    elif hoverReturn((app.mouseX, app.mouseY)): #return page
                        toGuide()
                        app.mousePressed = False
                # restarts game if the player has won or lost
                elif ((app.in_win or app.in_lose) and 
                      (pressedPlayAgain((app.mouseX, app.mouseY)))):
                    toStart()
                    app.reset()

    # detects hand motion if right or left hand in frame
    if (right_hand):
        right_is_throwing = detect_throw(right_hand,zR)
        right_is_catching = detect_catch(right_hand,zR_rev)
        right_is_swiping= detect_swipe(right_hand,RHX)
    if(left_hand):
        left_is_throwing = detect_throw(left_hand,zL)
        left_is_catching = detect_catch(left_hand,zL_rev)
        left_is_swiping = detect_swipe(left_hand,LHX)

    is_throwing = left_is_throwing or right_is_throwing
    is_catching = right_is_catching or left_is_catching
    is_swiping = right_is_swiping or left_is_swiping

    # detects special user motion
    if is_throwing:
        current_gesture = special_list[2]
    elif is_catching:
        current_gesture  = special_list[0]
        just_caught = True
    if just_caught == True and is_swiping:
        sequence_complete= True
        current_gesture = special_list[3]
        just_caught = False

    # detects two-hand battle motions
    if left_hand and right_hand:
        if (detect_fly(left_hand,right_hand)):
            current_gesture = move_list[0]
        elif (detect_fist_palm(left_hand,right_hand)):
            current_gesture = move_list[1]
        elif (detect_dragonBall(left_hand,right_hand)):
            current_gesture = move_list[2]
        elif (detect_triangle(left_hand,right_hand)):
            current_gesture = move_list[3]

    # convert frame from BGR (OpenCV) to RGB (Pygame)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # resize frame to fit Pygame screen
    frame = cv2.resize(frame, (target_width, target_height))

    # convert frame to Pygame surface
    frame = np.rot90(frame)
    frame = pygame.surfarray.make_surface(frame)

    # display camera feed on Pygame screen
    screen.blit(frame, (0, 0))

    # deals with actions in selection screen
    if app.in_select:
        mousePos = pygame.mouse.get_pos()
        instr_text, instr_rect = app.pokefont.render("CLICK TO CHOOSE", (0,0,0), 
                                                     size = 18)
        instr_rect.center = (450, 535)
        app.canvas.blit(instr_text, instr_rect)

        # displays text and arrow when mouse hovers over Tartanmon
        if hoverBulb(mousePos):
            app.canvas.blit(app.arrowImg, (140, 180))
            if app.bulbDead:
                warn_text, warn_rect = app.pokefont.render("FAINTED! CAN'T CHOOSE", 
                                                           (0,0,0), size = 18)
                warn_rect.center = (450, 565)
                app.canvas.blit(warn_text, warn_rect)
        elif hoverChar(mousePos):
            app.canvas.blit(app.arrowImg, (405, 180))
            if app.charDead:
                warn_text, warn_rect = app.pokefont.render("FAINTED! CAN'T CHOOSE", 
                                                           (0,0,0), size = 18)
                warn_rect.center = (450, 565)
                app.canvas.blit(warn_text, warn_rect)
        elif hoverSquirt(mousePos):
            app.canvas.blit(app.arrowImg, (680, 180))
            if app.squirtDead:
                warn_text, warn_rect = app.pokefont.render("FAINTED! CAN'T CHOOSE", 
                                                           (0,0,0), size = 18)
                warn_rect.center = (450, 565)
                app.canvas.blit(warn_text, warn_rect)
        else:
            app.canvas.blit(app.bg, (0,0))

        # diplays Tartanmon image
        if app.bulbDead:
            app.canvas.blit(app.bulbDeadImg, (88, 245))
        else:
            app.canvas.blit(app.bulbImg, (88, 245))
        if app.charDead:
            app.canvas.blit(app.charDeadImg, (375, 240))
        else: 
            app.canvas.blit(app.charImg, (375, 240))
        if app.squirtDead:
            app.canvas.blit(app.squirtDeadImg, (625, 240))
        else:
            app.canvas.blit(app.squirtImg, (625, 240))

    # deals with actions in battle screen
    if app.in_battle:
        if app.players_turn and not app.text_box_active:
            # throws if no active Tartanmon
            if app.curr_pokemon == None and current_gesture == 'Throw':
                app.trainer.throwing_ball = True
                spawn_player_mon()  # spawns Tartanmon
                if app.opponent is None:
                    spawn_opponent() # spawns opponent
            # cannot use next move until text box disappears
            elif app.curr_pokemon != None:
                if current_gesture in move_list: # if player uses move
                    use_player_move(current_gesture)
                hit_opponent()
            # returns back to Tartanmon selection screen
            if current_gesture == "Exit_sequence":
                toSelect()

        # opponents turn
        elif not app.players_turn and not app.text_box_active:
            use_opponent_move()
            hit_player()
            
        # trainer throwing animation
        if app.trainer.showing:
            draw_trainer()
            app.canvas.blit(app.trainer.animation[app.trainer.frame_index], 
                            (app.trainer.x, app.canvas_height - 300))

        # draws player's Tartanmon
        if app.curr_pokemon is not None:
            draw_player_mon()
        # draws opponent Tartanmon
        if app.opponent is not None:
            draw_opponent_mon()
        # draws top-left text box
        if app.text_box_active:
            draw_text_box()
        # checks if player has lost (all Tartanmon dead)
        if app.charDead and app.squirtDead and app.bulbDead:
            toLose()
        # checks if player has won (opponent dead)
        elif app.opponent_dead:
            toWin()
        # returns to selection screen if current Tartanmon is dead
        elif app.curr_pokemon_dead:
            toSelect()

    if app.opponent_dead: pass

    app.window.blit(app.canvas, (0,0))
    screen.blit(frame, (900 - target_width, 0))
    pygame.display.update()
    clock = pygame.time.Clock()
    clock.tick(60)

    # Update Pygame display
    pygame.display.flip()

    # Cap frame rate 
    pygame.time.Clock().tick(60)

# Release resources and quit Pygame
cap.release()
pygame.quit()