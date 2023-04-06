import pygame
import typing
import enum
import math
import datetime

import api

size = (0, 0)

pygame.init()

zermelo = None

username = ''
password = ''
tenant = 'gymnasiumnovum'

week_nr = str(int(datetime.datetime.now().strftime('%Y%U')) + 1)
week = None
print(week_nr)


class State(enum.IntEnum):
    username = enum.auto()
    password = enum.auto()
    login = enum.auto()  # logging into zermelo
    main = enum.auto()


state = State.username


try:
    with open('credentials.txt', 'r') as file:
        data = file.read()
        split = data.split('\n')
        if len(split) != 3:
            raise ValueError
        username = split[0]
        password = split[1]
        tenant = split[2]
        state = State.login
        zermelo = api.Api(username, password, tenant)
except FileNotFoundError:
    pass
except ValueError:
    pass


def loading_spinner(x: int, y: int):
    global screen, size, frame
    speed = .06

    s = size[1] // 10
    pygame.draw.rect(screen, (0, 0, 0), (x, y, s, s))

    # pygame.draw.lines(screen, (255, 255, 255), False, [
    #     (x + math.sin(frame * speed) * s / 2, y + math.cos(frame * speed) * s / 2),
    #     (x + math.sin(frame * speed + math.pi / 2) * s / 2, y + math.cos(frame * speed + math.pi / 2) * s / 2),
    #     (x + math.sin(frame * speed + math.pi) * s / 2, y + math.cos(frame * speed + math.pi) * s / 2)
    # ], size[1] // 30)

    circles = 7
    for i in range(circles):
        pygame.draw.circle(screen, (255, 255, 255),
                           (x + math.sin(frame * speed + i / circles * math.pi * ((frame + i / circles) * .01)) * s / 2,
                            y + math.cos(frame * speed + i / circles * math.pi * ((frame + i / circles) * .01)) * s / 2),
                           size[1] // 80)


pre_mouse_press = [False, False, False]
font = pygame.font.SysFont('ubuntu', 10)
big_font = pygame.font.SysFont('ubuntu', 20)


def resize():
    global size, font, big_font

    font = pygame.font.SysFont('ubuntu', size[1] // 30)
    big_font = pygame.font.SysFont('ubuntu', size[1] // 20)


screen = pygame.display.set_mode(size, pygame.RESIZABLE)
clock = pygame.time.Clock()
run = True
size = screen.get_size()  # different because (0, 0) makes it fit to the screen
resize()
frame = 0

while run:
    clock.tick(60)
    screen.fill((0, 0, 0))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        elif event.type == pygame.WINDOWRESIZED:
            size = screen.get_size()
            resize()

        elif event.type == pygame.TEXTINPUT:  # TODO: TEXTEDITING event
            if state == State.username:
                username += event.text
            if state == State.password:
                password += event.text

        elif event.type == pygame.KEYDOWN:
            if state == State.username:
                if event.key == pygame.K_BACKSPACE:
                    username = username[:-1]
                elif event.key == pygame.K_RETURN:
                    state = State.password
            elif state == State.password:
                if event.key == pygame.K_BACKSPACE:
                    password = password[:-1]
                elif event.key == pygame.K_RETURN:
                    state = State.login
                    zermelo = api.Api(username, password, tenant)

    if zermelo is not None:
        zermelo.update()
        week = zermelo.get(week_nr)

    if state != State.main:
        screen.blit(font.render(str(state)[6:], True, (255, 255, 255)), (0, 0))

    if state == State.username:
        screen.blit(big_font.render(username, True, (255, 255, 255)), (100, 100))
    elif state == State.password:
        screen.blit(big_font.render(username, True, (255, 255, 255)), (100, 100))
        screen.blit(big_font.render('#' * len(password), True, (255, 255, 255)), (100, 100 + size[1] // 20))
    elif state == State.login:
        loading_spinner(size[1] // 10, size[1] // 10)
        pygame.draw.rect(screen, (255, 255, 255),
                         (0, size[1] // 5, round(zermelo.state / zermelo.max_state * size[0]), size[1] // 20))
        if zermelo.state == zermelo.max_state:
            state = State.main

            with open('credentials.txt', 'w') as file:
                file.write(username + '\n' + password + '\n' + tenant)  # TODO: prompt the user if they want to store
        if not zermelo.successfull:
            if not zermelo.credentials_correct:
                state = State.username  # TODO: inform the user why they are suddenly back to the login screen
                username = ''
                password = ''
            else:
                zermelo = api.Api(username, password, tenant)  # TODO: notify user

    elif state == State.main:
        if week is not None:
            # print(week, week.appointments, week.raw)
            height = size[1] // 30
            width = size[0] // 7
            y = 0
            x = 0
            for appointment in week.appointments:
                # print(appointment.start.isoweekday(), appointment.start.hour + appointment.start.minute / 60)

                x = width * (appointment.start.isoweekday() - 1)
                y = round(height * (appointment.start.hour + appointment.start.minute / 60))
                h = round(height * (appointment.end.hour + appointment.end.minute / 60) - y)

                # y = round(height * (23 + 59 / 60))

                if appointment.valid:
                    c = (30, 30, 30)
                else:
                    c = (100, 0, 0)
                pygame.draw.rect(screen, c, (x, y, width, h))

                if appointment.cancelled:
                    c = (100, 100, 100)
                else:
                    c = (255, 255, 255)
                pygame.draw.rect(screen, c, (x, y, width, h), 1)

                screen.blit(font.render('a', True, (255, 255, 255)), (x, y))

                y += height
        else:
            loading_spinner(size[1] // 10, size[1] // 10)

    # screen.blit(font.render('Hello, World', True, (255, 255, 255)), (0, 0))
    # screen.blit(big_font.render('Hello, World', True, (255, 255, 255)), (0, size[1] // 30))

    pygame.display.update()
    frame += 1

pygame.quit()
