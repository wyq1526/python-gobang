import pygame as pg
import math
import time
WIDTH = 40
COLUMN = 15
ROW = 15
#界面、音频初始化
pg.init()
pg.mixer.init()
pg.mixer.music.load('music/bgm.mp3')
pg.mixer.music.set_volume(1)
pg.mixer.music.play()
interval = pg.mixer.Sound('music/point.wav')
interval.set_volume(1)
victory = pg.mixer.Sound('music/victory.wav')
victory.set_volume(1)
defeat = pg.mixer.Sound('music/defeat.wav')
defeat.set_volume(1)

list_ai = []
list_hu = []
list_sum = [] #双方下过的
list_all = [] #整个棋盘的店
next_step = [0, 0] #ai下一步下的位置
DEPTH = 1 #每次ai搜索的深度
CUT = 0
SEARCH = 0
#棋子形状的分数评估模型
score_shape = [
    (1, (0, 1, 1, 0, 0)),
    (1, (0, 0, 1, 1, 0)),
    (100, (1, 0, 1, 1, 0)),
    (100, (0, 1, 0, 1, 1)),
    (100, (1, 1, 0, 1, 0)),
    (100, (0, 1, 1, 0, 1)),
    (100, (1, 1, 1, 0, 0)),
    (100, (0, 0, 1, 1, 1)),
    (10000, (0, 1, 1, 1, 0)),
    (10000, (0, 1, 0, 1, 1, 0)),
    (10000, (0, 1, 1, 0, 1, 0)),
    (10000, (0, 1, 1, 1, 1)),
    (10000, (1, 1, 1, 1, 0)),
    (10000, (1, 0, 1, 1, 1)),
    (10000, (1, 1, 1, 0, 1)),
    (10000, (1, 1, 0, 1, 1)),
    (1000000, (0, 1, 1, 1, 1, 0)),
    (100000000, (1, 1, 1, 1, 1))
]

def ai():
    global  CUT
    global  SEARCH
    CUT = 0
    SEARCH = 0
    score = neg_max_search(-9999999999, 9999999999, True, DEPTH)
    print('本次得分:', score)
    print('剪枝数:', CUT)
    print('搜索数:', SEARCH )
    return next_step[0], next_step[1]

def neg_max_search(alpha, beta, is_ai, depth):
    if game_over(list_ai) or game_over(list_hu) or depth == 0:
        total_score = evaluate(is_ai)
        return total_score

    #计算空余位置的集合
    blank_list = list(set(list_all).difference(set(list_sum)))
    #按远近排序
    near_order(blank_list)
    for next in blank_list:
        global SEARCH
        SEARCH += 1
        if not has_neightnor(next):
            continue
        if is_ai:
            list_ai.append(next)
        else:
            list_hu.append(next)
        list_sum.append(next)

        value = -neg_max_search(-beta, -alpha, not is_ai, depth - 1)
        if is_ai:
            list_ai.remove(next)
        else:
            list_hu.remove(next)
        list_sum.remove(next)
        #下一层的值比这一层的最大值要大
        if value > alpha:
            #确定下一步要下的棋子的位置
            if depth == DEPTH:
                next_step[0] = next[0]
                next_step[1] = next[1]
            #下一层的值比这一层的最小值大，剪枝
            if value >= beta:
                global  CUT
                CUT += 1
                return beta
            alpha = value

    return alpha#得分的最大值


# 将上次落点周围的点放在前面
def near_order(list_blank):
    last = list_sum[-1] #最后一次的落点位置
    for x in range(-1, 2):
        for y in range(-1, 2):
            if x == 0 and y == 0:
                continue
            elif (last[0] + x, last[1] + y) in list_blank:
                list_blank.remove((last[0] + x, last[1] + y))
                list_blank.insert(0, (last[0] + x, last[1] + y))#插入第一个

def has_neightnor(item):
    for x in range(-1, 2):
        for y in range(-1, 2):
            if x == 0 and y == 0:
                continue
            elif(item[0] + x, item[1] + y) in list_sum:#有邻居
                return True
    return False

#评估函数
def evaluate(is_ai):
    #当前局面对于一方的的总得分值
    if is_ai:
        self_list = list_ai
        enemy_list = list_hu
    else:
        self_list = list_hu
        enemy_list = list_ai

    all_score_shape_direct = []
    self_score = 0 #自己当前局面的总分数
    for dot in self_list:
        x = dot[0]
        y = dot[1]
        self_score += calculate(x, y, 1, 0, self_list, enemy_list, all_score_shape_direct)
        self_score += calculate(x, y, 0, 1, self_list, enemy_list, all_score_shape_direct)
        self_score += calculate(x, y, 1, 1, self_list, enemy_list, all_score_shape_direct)
        self_score += calculate(x, y, 1, -1, self_list, enemy_list, all_score_shape_direct)


    enemy_all_score_shape_direct = []
    enemy_score = 0  # 自己当前局面的总分数
    for dot in enemy_list:
        x = dot[0]
        y = dot[1]
        enemy_score += calculate(x, y, 1, 0, enemy_list, self_list, enemy_all_score_shape_direct)
        enemy_score += calculate(x, y, 0, 1, enemy_list, self_list, enemy_all_score_shape_direct)
        enemy_score += calculate(x, y, 1, 1, enemy_list, self_list, enemy_all_score_shape_direct)
        enemy_score += calculate(x, y, 1, -1, enemy_list, self_list, enemy_all_score_shape_direct)

    #规则待改善
    total_score = self_score - enemy_score
    return total_score


#计算某个点所在棋子形状的得分值
def calculate(x, y, direct_x, direct_y, self_list, enemy_list, all_score_shape_direct):
    extra_score = 0
    maxscore_shape = (-100, None)

    #该点在此方向已经加入了某种形状的计算，不重复计算
    for item in all_score_shape_direct:
        if (x, y) in item[1] and direct_x == item[2][0] and direct_y == item[2][1]:
            return 0

    #在落点位置的[-5, 5]的范围内查找得分形状，偏移量-5到0范围内，遍历0到5
    for offset in range(-5, 1):
        shape = [] #记录每种偏移量时的形状
        for i in range(0, 6):
            #敌方棋子
            real_offset = i + offset
            if x + real_offset * direct_x < 0 or x + real_offset * direct_x > COLUMN or y + real_offset * direct_y < 0 or y + real_offset * direct_y > ROW:
                break#超出范围
            if (x + real_offset * direct_x, y + real_offset * direct_y) in enemy_list:
                shape.append(-1)
            #我方棋子
            elif(x + real_offset * direct_x, y + real_offset * direct_y) in self_list:
                shape.append(1)
            #空位
            else:
                shape.append(0)
        shape_len5_1 = None
        shape_len5_2 = None
        shape_len6 = None
        #将数组转化为元组
        if len(shape)== 5:
            shape_len5_1 = tuple(shape)
        elif len(shape) == 6:
            shape_len6 = tuple(shape)
            shape_len5_1 = tuple(shape[:5])
            shape_len5_2 = tuple(shape[1:])
        else:#长度小于5不能成功匹配
            continue
        score5 = 0
        score6 = 0
        for item in score_shape:
            if shape_len5_1 == item[1] or shape_len5_2 == item[1]:
                score5 = max(score5, item[0])
            if shape_len6 == item[1]:
                score6 = item[0]
        # 长度为5的棋子形状
        if score5 > 0 and score5 > score6 and score5 > maxscore_shape[0]:
            maxscore_shape = (
                score5,
                (
                    (x + (offset + 0) * direct_x, y + (offset + 0) * direct_y),
                    (x + (offset + 1) * direct_x, y + (offset + 1) * direct_y),
                    (x + (offset + 2) * direct_x, y + (offset + 2) * direct_y),
                    (x + (offset + 3) * direct_x, y + (offset + 3) * direct_y),
                    (x + (offset + 4) * direct_x, y + (offset + 4) * direct_y)
                ),
                (direct_x, direct_y)
            )
        # 长度为6的棋子形状
        elif score6 > 0 and score6 > score5 and score6 > maxscore_shape[0]:
            maxscore_shape = (
                score6,
                (
                    (x + (offset + 0) * direct_x, y + (offset + 0) * direct_y),
                    (x + (offset + 1) * direct_x, y + (offset + 1) * direct_y),
                    (x + (offset + 2) * direct_x, y + (offset + 2) * direct_y),
                    (x + (offset + 3) * direct_x, y + (offset + 3) * direct_y),
                    (x + (offset + 4) * direct_x, y + (offset + 4) * direct_y),
                    (x + (offset + 5) * direct_x, y + (offset + 5) * direct_y)
                ),
                (direct_x, direct_y)
            )
    #如果两个形状有相交的点，整个棋子的布局的得分增加
    if maxscore_shape[0] > 0:
        for item in all_score_shape_direct:
            for dot1 in item[1]:
                for dot2 in maxscore_shape[1]:
                    #活三以上级别的相交，也可以适当修改加分规则
                    if maxscore_shape[0] >= 100 and item[0] >= 100 and dot1 == dot2:
                        #额外获得加分相当于相交的两个个自得分加倍
                        extra_score += item[0] + maxscore_shape[0]
        #将maxscore_shape加入all_score_shape_direct
        all_score_shape_direct.append(maxscore_shape)
    return extra_score + maxscore_shape[0]

#游戏结束
def game_over(list):
    for col in range(COLUMN + 1):
        for row in range(ROW + 1):
            if row < ROW - 3 and (col, row) in list and (col, row + 1) in list and (col, row + 2) in list\
            and (col, row + 3) in list and (col, row + 4) in list:
                return True
            elif col < COLUMN - 3 and row < ROW - 3 and (col, row) in list and (col + 1, row + 1) in list and (col + 2, row + 2) in list\
            and (col + 3, row + 3) in list and (col + 4, row + 4) in list:
                return True
            elif col < COLUMN - 3 and row > 3 and (col, row) in list and (col + 1, row - 1) in list and (col + 2, row - 2) in list\
            and (col + 3, row - 3) in list and (col + 4, row - 4) in list:
                return True
            elif col < COLUMN - 3 and (col, row) in list and (col + 1, row) in list and (col + 2, row) in list\
            and (col + 3, row) in list and (col + 4, row) in list:
                return True
    return False

def board():#绘制界面
    pg.display.set_caption('五子棋')
    screen = pg.display.set_mode((WIDTH*(COLUMN+1), WIDTH*(ROW+1)))
    screen.fill((249, 214, 91))
    i1 = WIDTH/2

    while i1 <= WIDTH * (COLUMN + 1):
        pg.draw.line(screen, (0, 0, 0), (i1, WIDTH/2), (i1, WIDTH * (COLUMN + 1/2)), 2)
        i1 = i1 + WIDTH
    i2 = WIDTH/2

    while i2 <= WIDTH * (ROW + 1):
        pg.draw.line(screen, (0, 0, 0), (WIDTH/2, i2), (WIDTH * (ROW + 1/2), i2), 2)
        i2 = i2 + WIDTH
    return screen

def game_body():
    gobang = board()
    tip = pg.font.Font(None, 30)
    tip_mes = tip.render('press K_DOWN to play first, otherwise second', True, (0, 0, 0))
    gobang.blit(tip_mes, (10, 0, 100, 20))
    pg.display.flip()
    ai_turn = None
    font = pg.font.Font(None, 40)
    count = 0
    last_ai_step = None
    while True:
        for e in pg.event.get():
            pg.display.flip()
            if e.type == pg.KEYDOWN and ai_turn is None:
                if e.key == pg.K_DOWN:
                    #人先下
                    ai_turn = False
                    is_first = False
                else:
                    #AI先下
                    ai_turn = True
                    is_first = True
                gobang = board()
            else:
                if ai_turn is not None:
                    while True:
                        if game_over(list_ai):
                            mes = font.render('AI win, press K_UP to play again, otherwise quit ', True, (0, 0, 0))
                            gobang.blit(mes, (10, 50, 400, 100))
                            pg.display.flip()
                            pg.mixer.music.pause()
                            defeat.play()
                            while True:
                                for ev in pg.event.get():
                                    if ev.type == pg.KEYDOWN:
                                        if ev.key == pg.K_UP:
                                            return True
                                        else:
                                            return False
                        if game_over(list_hu):
                            mes = font.render('You win, press up to play again, otherwise quit', True, (0, 0, 0))
                            gobang.blit(mes, (10, 50, 400, 100))
                            pg.display.flip()
                            pg.mixer.music.pause()
                            victory.play()
                            while True:
                                for ev in pg.event.get():
                                    if ev.type == pg.KEYDOWN:
                                        if ev.key == pg.K_UP:
                                            return True
                                        else:
                                            return False
                        if len(list_sum) != 0 and len(list_sum) == len(list_all):
                            mes = font.render('Deuce, press up to play again, otherwise quit', True, (0, 0, 0))
                            gobang.blit(mes, (10, 50, 400, 100))
                            pg.display.flip()
                            while True:
                                for ev in pg.event.get():
                                    if ev.type == pg.KEYDOWN:
                                        if ev.key == pg.K_UP:
                                            return True
                                        else:
                                            return False
                        if ai_turn:
                            count += 1
                            start = time.time()
                            if list_sum == []:
                                col, row = int(COLUMN / 2), int(ROW / 2)
                            else:
                                col, row = ai()
                            end = time.time()
                            print('第'+str(count)+'回合：', col, row)
                            print('本次搜索用时' + str(int(end - start)) + 's')

                            if not (col, row) in list_sum:
                                x = int((col + 1 / 2) * WIDTH)
                                y = int((row + 1 / 2) * WIDTH)
                                if is_first == True:#AI先下
                                    ai_color = (0, 0, 0)
                                    fork_color = (255, 255, 255)
                                else:
                                    ai_color = (255, 255, 255)
                                    fork_color = (0, 0, 0)
                                pg.draw.circle(gobang, ai_color, (x, y), 15, 0)
                                pg.draw.line(gobang, fork_color, (x - 7, y - 7), (x + 7, y + 7), 3)
                                pg.draw.line(gobang, fork_color, (x + 7, y - 7), (x - 7, y + 7), 3)
                                if last_ai_step is not None:
                                    last_x = int((last_ai_step[0] + 1 / 2) * WIDTH)
                                    last_y = int((last_ai_step[1] + 1 / 2) * WIDTH)
                                    pg.draw.circle(gobang, ai_color, (last_x, last_y), 15, 0)
                                last_ai_step = [col, row]
                                pg.display.flip()
                                interval.play()
                                ai_turn = False
                                list_ai.append((col, row))
                                list_sum.append((col, row))
                                print('list_sum:', list_sum, '\n\n')
                        else:
                            pg.event.wait()
                            if pg.mouse.get_pressed()[0] == 1:
                                x, y = pg.mouse.get_pos()
                                col = math.floor(x / WIDTH)
                                row = math.floor(y / WIDTH)
                                print('人:第', count, '回合:', col, row)
                                if not (col, row) in list_sum:
                                    x = int((col + 1 / 2) * WIDTH)
                                    y = int((row + 1 / 2) * WIDTH)
                                    if is_first == True:  # AI先下
                                        hu_color = (255, 255, 255)
                                    else:
                                        hu_color = (0, 0, 0)
                                    pg.draw.circle(gobang, hu_color, (x, y), 15, 0)
                                    pg.display.flip()
                                    interval.play()
                                    ai_turn = True
                                    list_hu.append((col, row))
                                    list_sum.append((col, row))


def main():
    #初始化list_all
    for i in range(COLUMN+1):
        for j in range(ROW+1):
            list_all.append((i, j))
    while True:
        print('请选择难度：\n简单[1]\n一般[2]\n困难[3](等待时间会很长)\n')
        try:
            global DEPTH
            DEPTH = int(input('请输入难度'))
            if DEPTH > 3:
                DEPTH = 3
            if DEPTH < 0:
                DEPTH = 1
        except:
            print('未正确输入数字,已经按照简单模式进行')
        global list_ai
        list_ai = []
        global list_hu
        list_hu = []
        global list_sum
        list_sum = []
        if not game_body():
            break










if __name__ == '__main__':
    main()