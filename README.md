# TrackyNotes

### セットアップ
python3.6環境で検証済み
```bash
git clone git@github.com:kajiwara555/TrackyNotes.git
cd TrackyNotes
pip install -r requirements.py
```

### 付箋の作成
付箋の枠線が不要な場合は下記設定ファイルの'write_outer_rectangle'をFalseにしてから実行
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
100cm × 75cmで印刷して切り取ると付箋が完成（イラレやwordを使う）

### 付箋の認識
