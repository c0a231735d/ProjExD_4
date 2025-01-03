import math
import os
import random
import sys
import time
import pygame as pg

WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    """
    orgから見て，dstがどこにあるかを計算し，方向ベクトルをタプルで返す
    引数1 org：爆弾SurfaceのRect
    引数2 dst：こうかとんSurfaceのRect
    戻り値：orgから見たdstの方向ベクトルを表すタプル
    """
    x_diff, y_diff = dst.centerx-org.centerx, dst.centery-org.centery
    norm = math.sqrt(x_diff**2+y_diff**2)
    return x_diff/norm, y_diff/norm


class Bird(pg.sprite.Sprite):
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, +1),
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (+1, 0),
    }

    def __init__(self, num: int, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 xy：こうかとん画像の位置座標タプル
        """
        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん
        self.imgs = {
            (+1, 0): img,  # 右
            (+1, -1): pg.transform.rotozoom(img, 45, 0.9),  # 右上
            (0, -1): pg.transform.rotozoom(img, 90, 0.9),  # 上
            (-1, -1): pg.transform.rotozoom(img0, -45, 0.9),  # 左上
            (-1, 0): img0,  # 左
            (-1, +1): pg.transform.rotozoom(img0, 45, 0.9),  # 左下
            (0, +1): pg.transform.rotozoom(img, -90, 0.9),  # 下
            (+1, +1): pg.transform.rotozoom(img, -45, 0.9),  # 右下
        }
        self.dire = (+1, 0)
        self.image = self.imgs[self.dire]
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.speed = 10
        self.state = "normal"  #こうかとんの状態を初期化
        self.hyper_life = 0    #発動時間の変数の初期化

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.image, self.rect)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        current_speed = self.speed

        # 左Shiftキーが押されている場合、スピードを2倍に
        if key_lst[pg.K_LSHIFT]:
            current_speed = 20
        
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rect.move_ip(current_speed*sum_mv[0], current_speed*sum_mv[1])
        if check_bound(self.rect) != (True, True):
            self.rect.move_ip(-current_speed*sum_mv[0], -current_speed*sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)
            self.image = self.imgs[self.dire]
        if self.state == "hyper":
            self.image = pg.transform.laplacian(self.image)    #無敵状態発動中のこうかとんイメージ
            self.hyper_life -= 1
            if self.hyper_life < 0:
                self.state = "normal"    #無敵状態の終了
        screen.blit(self.image, self.rect)
        


    


class Bomb(pg.sprite.Sprite):
    """
    爆弾に関するクラス
    """
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]

    def __init__(self, emy: "Enemy", bird: Bird):
        """
        爆弾円Surfaceを生成する
        引数1 emy：爆弾を投下する敵機
        引数2 bird：攻撃対象のこうかとん
        """
        super().__init__()
        rad = random.randint(10, 50)  # 爆弾円の半径：10以上50以下の乱数
        self.image = pg.Surface((2*rad, 2*rad))
        color = random.choice(__class__.colors)  # 爆弾円の色：クラス変数からランダム選択
        pg.draw.circle(self.image, color, (rad, rad), rad)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        # 爆弾を投下するemyから見た攻撃対象のbirdの方向を計算
        self.vx, self.vy = calc_orientation(emy.rect, bird.rect)  
        self.rect.centerx = emy.rect.centerx
        self.rect.centery = emy.rect.centery+emy.rect.height//2
        self.speed = 6

    def update(self):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Beam(pg.sprite.Sprite):
    """
    ビームに関するクラス
    """
    def __init__(self, bird: Bird, angle0: float = 0):
        """
        ビーム画像Surfaceを生成する
        引数:
        - bird: ビームを放つこうかとん
        - angle0: 回転角度（デフォルトは0）
        """
        super().__init__()
        self.vx, self.vy = bird.dire
        angle = math.degrees(math.atan2(-self.vy, self.vx)) + angle0
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/beam.png"), angle, 1.0)
        self.vx = math.cos(math.radians(angle))
        self.vy = -math.sin(math.radians(angle))
        self.rect = self.image.get_rect()
        self.rect.centery = bird.rect.centery + bird.rect.height * self.vy
        self.rect.centerx = bird.rect.centerx + bird.rect.width * self.vx
        self.speed = 10

    def update(self):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        """
        self.rect.move_ip(self.speed * self.vx, self.speed * self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()



class Explosion(pg.sprite.Sprite):
    """
    爆発に関するクラス
    """
    def __init__(self, obj: "Bomb|Enemy", life: int):
        """
        爆弾が爆発するエフェクトを生成する
        引数1 obj：爆発するBombまたは敵機インスタンス
        引数2 life：爆発時間
        """
        super().__init__()
        img = pg.image.load(f"fig/explosion.gif")
        self.imgs = [img, pg.transform.flip(img, 1, 1)]
        self.image = self.imgs[0]
        self.rect = self.image.get_rect(center=obj.rect.center)
        self.life = life

    def update(self):
        """
        爆発時間を1減算した爆発経過時間_lifeに応じて爆発画像を切り替えることで
        爆発エフェクトを表現する
        """
        self.life -= 1
        self.image = self.imgs[self.life//10%2]
        if self.life < 0:
            self.kill()


class Enemy(pg.sprite.Sprite):
    """
    敵機に関するクラス
    """
    imgs = [pg.image.load(f"fig/alien{i}.png") for i in range(1, 4)]
    
    def __init__(self):
        super().__init__()
        self.image = pg.transform.rotozoom(random.choice(__class__.imgs), 0, 0.8)
        self.rect = self.image.get_rect()
        self.rect.center = random.randint(0, WIDTH), 0
        self.vx, self.vy = 0, +6
        self.bound = random.randint(50, HEIGHT//2)  # 停止位置
        self.state = "down"  # 降下状態or停止状態
        self.interval = random.randint(50, 300)  # 爆弾投下インターバル

    def update(self):
        """
        敵機を速度ベクトルself.vyに基づき移動（降下）させる
        ランダムに決めた停止位置_boundまで降下したら，_stateを停止状態に変更する
        引数 screen：画面Surface
        """
        if self.rect.centery > self.bound:
            self.vy = 0
            self.state = "stop"
        self.rect.move_ip(self.vx, self.vy)


class Gravity(pg.sprite.Sprite):
    """
    重力場に関するクラス
    """
    def __init__(self,life):
        super().__init__()
        self.image = pg.Surface((1100,650))
        self.rect = self.image.get_rect()
        pg.draw.rect(self.image,(0, 0, 0),(0, 0, 1100, 650))
        self.image.set_alpha(128)
        self.life = life

    def update(self):
        self.life -= 1
        if self.life <= 0:
            self.kill()

class Score:
    """
    打ち落とした爆弾，敵機の数をスコアとして表示するクラス
    爆弾：1点
    敵機：10点
    """
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.value = 0
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT-50

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)


class EMP:
    """
    EMP（電磁パルス）に関するクラス
    """
    def __init__(self, emys: pg.sprite.Group, bombs: pg.sprite.Group, screen: pg.Surface): # コンストラクタ
        """
        引数：
        emys：Enemyインスタンスのグループ
        bombs：Bombインスタンスのグループ
        screen：画面Surface
        """
        self.emys = emys # 敵機グループ
        self.bombs = bombs # 爆弾グループ
        self.screen = screen # 画面Surface

    def activate(self, score: Score): # メソッド
        """
        EMPを発動する
        引数：
        score：スコアクラスのインスタンス
        """
        if score.value >= 20:  # スコアが20以上の場合のみ発動可能
            score.value -= 20  # スコアを20消費
            # 画面全体に黄色の矩形を表示（0.05秒）
            overlay = pg.Surface((WIDTH, HEIGHT), pg.SRCALPHA) # 透明なSurface
            overlay.fill((255, 255, 0, 100))  # 半透明の黄色
            self.screen.blit(overlay, (0, 0)) # 画面に表示
            pg.display.update() # 画面更新
            time.sleep(0.05) # 0.05秒待機
            # 敵機を無効化
            for emy in self.emys: # 敵機グループの各インスタンスに対して
                emy.interval = float('inf')  # 爆弾投下不可
                emy.image = pg.transform.laplacian(emy.image)  # ラプラシアンフィルタ適用
            # 爆弾を無効化
            for bomb in self.bombs: # 爆弾グループの各インスタンスに対して
                bomb.speed //= 2  # 速度を半減
                bomb.kill()  # 爆弾を即時消去

class NeoBeam:
    """
    複数方向にビームを発射するクラス
    """
    def __init__(self, bird: Bird, num: int):
        """
        NeoBeamを生成する
        引数:
        - bird: こうかとん
        - num: ビームの数
        """
        self.bird = bird
        self.num = num

    def gen_beams(self) -> list[Beam]:
        """
        ビームを複数生成してリストで返す
        """
        step = 100 // (self.num - 1)  # ビーム間の角度ステップを計算
        angles = range(-50, 51, step)  # -50度から+50度までの角度を生成
        beams = [Beam(self.bird, angle) for angle in angles]
        return beams


class Shield(pg.sprite.Sprite):
    """
    防御壁に関するクラス
    """
    def __init__(self, bird: Bird, life: int):
        """
        防御壁を生成する
        引数:
        - bird: こうかとんのインスタンス
        - life: 防御壁の持続時間（フレーム数）
        """
        super().__init__()
        width, height = 20, bird.rect.height * 2  # 防御壁の幅と高さ
        self.image = pg.Surface((width, height), pg.SRCALPHA)  # 透明度をサポート
        pg.draw.rect(self.image, (0, 0, 255), (0, 0, width, height))  # 青い矩形
        self.rect = self.image.get_rect()

        # こうかとんの向きを取得して配置
        vx, vy = bird.dire
        angle = math.degrees(math.atan2(-vy, vx))
        self.image = pg.transform.rotozoom(self.image, angle, 1.0)
        offset_x = vx * bird.rect.width
        offset_y = vy * bird.rect.height
        self.rect.center = bird.rect.centerx + offset_x, bird.rect.centery + offset_y

        self.life = life  # 防御壁の持続時間

    def update(self):
        """
        防御壁の持続時間を減算し、0未満になったら削除する
        """
        self.life -= 1
        if self.life < 0:
            self.kill()


def main():
    pg.display.set_caption("真！こうかとん無双")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load(f"fig/pg_bg.jpg")
    score = Score()

    bird = Bird(3, (900, 400))
    bombs = pg.sprite.Group()
    beams = pg.sprite.Group()
    exps = pg.sprite.Group()
    emys = pg.sprite.Group()
    gravitys = pg.sprite.Group()  # 重力波のグループ
    emp = EMP(emys, bombs, screen)  # EMPインスタンスの生成
    shields = pg.sprite.Group()  # 防御壁グループ

    tmr = 0
    clock = pg.time.Clock()
    while True:
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
            if event.type == pg.KEYDOWN: # キー押下時の処理
                if event.key == pg.K_SPACE: # スペースキー押
                    beams.add(Beam(bird))
                if event.key == pg.K_e:  # 「E」キー押下でEMP発動
                    emp.activate(score) # EMP発動

            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                beams.add(Beam(bird))
            if event.type == pg.KEYDOWN and event.key == pg.K_RSHIFT:
                if score.value > 100:       #スコアが100以上なら
                    score.value -= 100      #スコア100消費して
                    bird.state = "hyper"    #こうかとんハイパーモードへ移行
                    bird.hyper_life = 500   #発動時間は500フレーム
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE and key_lst[pg.K_LSHIFT]:
                # 左Shiftキーを押しながらスペースキーを押下
                num_beams = 5  # 発射するビームの数（例: 5）
                neobeam = NeoBeam(bird, num_beams)
                beams.add(*neobeam.gen_beams())  # Beamグループに追加

            if event.type == pg.KEYDOWN and event.key == pg.K_s:
                if score.value >= 50 and len(shields) == 0:  # スコア50以上、かつ防御壁が存在しない場合
                    score.value -= 50  # スコアを消費
                    shields.add(Shield(bird, 400))  # 防御壁を生成（400フレーム)

            if key_lst[pg.K_RETURN] and score.value >= 200:
                gravitys.add(Gravity(400))  # 重量場を生成
                score.value -= 200
        screen.blit(bg_img, [0, 0])

        if tmr % 200 == 0:  # 200フレームに1回，敵機を出現させる
            emys.add(Enemy()) # 敵機を生成

        for emy in emys:
            if emy.state == "stop" and tmr % emy.interval == 0: # 敵機が停止状態で，爆弾投下インターバルに達した場合
                bombs.add(Bomb(emy, bird))

        for emy in pg.sprite.groupcollide(emys, beams, True, True).keys(): # 敵機とビームの衝突判定
            exps.add(Explosion(emy, 100)) # 爆発エフェクトを生成
            score.value += 10 # スコアを10加算
            bird.change_img(6, screen) # 敵機撃破画像に変更
        for emy in pg.sprite.groupcollide(emys, gravitys, True, False).keys():  # 重力場と衝突した敵機のリスト
            exps.add(Explosion(emy, 100))  # 爆発エフェクト
            score.value += 10  # 10点アップ
            bird.change_img(6, screen)  # こうかとん喜びエフェクト

        for bomb in pg.sprite.groupcollide(bombs, gravitys, True, False).keys():  # 重力場と衝突した敵機のリスト
            exps.add(Explosion(bomb, 100))  # 爆発エフェクト
            score.value += 1  # 1点アップ
            bird.change_img(6, screen)  # こうかとん喜びエフェクト

        for bomb in pg.sprite.groupcollide(bombs, beams, True, True).keys():  # ビームと衝突した爆弾リスト
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            score.value += 1  # 1点アップ

        for bomb in pg.sprite.spritecollide(bird, bombs, True):  # こうかとんと衝突した爆弾リスト
            if bird.state == "hyper":              #こうかとんがハイパー状態なら
                exps.add(Explosion(bomb, 50))      #死なないで、爆発エフェクト付与
                score.value += 1                   #スコア1加算
            else: 
                bird.change_img(8, screen)  # こうかとん悲しみエフェクト
                score.update(screen)
                pg.display.update()
                time.sleep(2)
                return
        for bomb in pg.sprite.spritecollide(bird, bombs, True):
            bird.change_img(8, screen) # 爆発画像に変更
            score.update(screen) # スコアを画面に表示
            pg.display.update() # 画面更新
            time.sleep(2) # 2秒待機
            return
        
        for shield in shields:
            for bomb in pg.sprite.groupcollide(shields, bombs, False, True).values():
                exps.add(Explosion(bomb[0], 50))  # 爆発エフェクト


        bird.update(key_lst, screen)
        beams.update()
        beams.draw(screen)
        emys.update()
        emys.draw(screen)
        bombs.update()
        bombs.draw(screen)
        exps.update()
        exps.draw(screen)
        gravitys.update()
        gravitys.draw(screen)
        score.update(screen)
        shields.update()
        shields.draw(screen)
        pg.display.update()
        tmr += 1
        clock.tick(50)

if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
