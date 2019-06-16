###  概要
東京大学苗村研究室の研究成果である、TrackyNotesのソースコード。
論文は[こちら](https://www.jstage.jst.go.jp/article/his/20/1/20_57/_article/-char/ja)


### セットアップ
python3.6環境で検証済み
```bash
git clone git@github.com:kajiwara555/TrackyNotes.git
cd TrackyNotes
pip install -r requirements.py
```

### 付箋の作成
付箋の枠線が不要な場合は下記設定ファイルの`write_outer_rectangle`をFalseにしてから実行
```
config/postit_config.yaml
```
付箋作成コマンド
```bash
python ./tasks/make_postit.py
```
実行すると下記ディレクトリに付箋の画像が生成される
```
datas/postit
```
100cm × 75cmで印刷して切り取ると付箋が完成（サイズを指定して印刷するにはイラレやwordを使う）

### 付箋の認識
#### 認識の実行
1. サンプル動画として下記をダウンロード
https://drive.google.com/file/d/1ZfCmGj0zu9JNFXdfwths9e1-wNELjabJ/view?usp=sharing

なお、このファイルは論文のとおりの条件で作成している
- カメラ: GoPro Hero4 Black
- 解像度: 4K
- カメラと付箋の距離: 70cm

2. ダウンロードしたtest.MP4を下記ディレクトリに配置
```$xslt
datas/movie/test.MP4
```

3. コードを実行
```bash
python ./tasks/analyse.py 220 30
```
- 第1引数: 位置合わせマーカーの面積(解像度やカメラの距離によって変わる。今回の動画では220が最適。)
- 第2引数: 動画のfps

実行すると画面が現れて
```
Please select left-top and right-down
```
と表示されるので、模造紙の左上と右下をクリックし、Enterキーを押す。

すると左上から右下までの長方形部分が模造紙部分として認識され、その範囲のみが
付箋の探索範囲となる。

#### 結果の確認
認識された結果は、下記ディレクトリに配置される動画で確認することができる。
```
datas/movie_out/OUT.avi
```
また、認識結果は下記csvファイルにも記録される
```
# 各付箋の1秒ごとの位置を記録
datas/csv/every_second.csv
# 各付箋のid、初登場時刻、移動時刻、回転時刻を記録
datas/csv/final.csv
```