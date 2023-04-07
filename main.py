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

week_nr = int(datetime.datetime.now().strftime('%Y%U')) + 1
week = None
print(week_nr)

information_list = []
force_login = False

scroll_offset = 0


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

        force_login = True

except FileNotFoundError:
    pass
except ValueError:
    pass


def is_now_in_time_period(start, end, now):
    if start < end:
        return start <= now <= end
    else:
        return now >= start or now <= end


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
                            y + math.cos(
                                frame * speed + i / circles * math.pi * ((frame + i / circles) * .01)) * s / 2),
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
            elif state == State.main:
                if event.key == pygame.K_LEFT:
                    week_nr -= 1
                elif event.key == pygame.K_RIGHT:
                    week_nr += 1
                elif event.key == pygame.K_r:
                    week_nr = int(datetime.datetime.now().strftime('%Y%U')) + 1
        if event.type == pygame.MOUSEWHEEL:
            scroll_offset += event.y * 20

    if zermelo is not None:
        zermelo.update()
        week = zermelo.get(str(week_nr))

    if state != State.main:
        screen.blit(font.render(str(state)[6:] + ("..." if not force_login else "... > saved credentials"), True,
                                (255, 255, 255)), (0, 0))

        y = 420

        for message in information_list:
            screen.blit(font.render(message, True, (255, 255, 255)), (0, y))
            y += 27.5

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
                information_list.append("Failed to login!")
            else:
                zermelo = api.Api(username, password, tenant)  # TODO: notify user
                information_list.append("Successful login!")

    elif state == State.main:
        if week is not None:
            height_offset = 30
            # print(week, week.appointments, week.raw)
            # height = size[1] // 30
            height = (size[1] + 1) * 2 // 30 + height_offset
            width = size[0] // 7
            y = 0
            x = 0

            # display current week
            screen.blit(font.render(str(week_nr), True, (255, 255, 255)), (5, 0))

            # display current time
            screen.blit(
                font.render(datetime.datetime.strftime(datetime.datetime.now(), '%H:%M:%S'), True, (255, 255, 255)),
                (width * 6.575, 5))

            for appointment in week.appointments:

                # print(appointment.start.isoweekday(), appointment.start.hour + appointment.start.minute / 60)

                x = (width + 0.3) * (appointment.start.isoweekday() - 1)
                y = round(height * (appointment.start.hour + appointment.start.minute / 60)) - 600 + scroll_offset
                h = round(height * (appointment.end.hour + appointment.end.minute / 60) - y) + height_offset

                # y = round(height * (23 + 59 / 60))

                if len(appointment.subjects) <= 0 and len(appointment.teachers) <= 0:
                    continue

                if appointment.valid:

                    if int(datetime.datetime.strptime(str(appointment.start), '%Y-%m-%d %H:%M:%S').strftime('%d')) == datetime.date.today().day and is_now_in_time_period(datetime.time(appointment.start.hour, appointment.start.minute), datetime.time(appointment.end.hour, appointment.end.minute), datetime.datetime.now().time()):
                        if appointment.cancelled:
                            c = (125, 50, 50)
                        else:
                            c = (80, 80, 175)
                    else:
                        if appointment.cancelled:
                            c = (75, 30, 30)
                        else:
                            c = (30, 30, 30)
                else:
                    c = (100, 0, 0)
                pygame.draw.rect(screen, c, (x, y, width, h))

                if appointment.cancelled:
                    c = (255, 100, 100)
                else:
                    c = (255, 255, 255)
                pygame.draw.rect(screen, c, (x, y, width, h), 1)

                subjects = ', '.join(appointment.subjects)
                teachers = ', '.join(appointment.teachers)
                locations = ', '.join(appointment.locations)

                screen.blit(font.render(subjects
                                        + (' - ' if teachers != '' else '') + teachers
                                        + (' > ' if locations != '' else '') + locations + (
                                            ' (V)' if appointment.cancelled else ''), True, (255, 255, 255)),
                            (x + 5, y))
                screen.blit(font.render((datetime.datetime.strftime(appointment.start, "%H:%M")
                                         + " ~ " + datetime.datetime.strftime(appointment.end, "%H:%M")), True,
                                        (255, 255, 255)), (x + 5, y + 27.5))

                y += height


        else:
            loading_spinner(size[1] // 10, size[1] // 10)

    # screen.blit(font.render('Hello, World', True, (255, 255, 255)), (0, 0))
    # screen.blit(big_font.render('Hello, World', True, (255, 255, 255)), (0, size[1] // 30))

    pygame.display.update()
    frame += 1

pygame.quit()
