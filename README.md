# Tower Defense Runner

大量の敵が決められた道を進み、プレイヤー側の兵士が自動射撃で敵・数字ゲート・武器コンテナを破壊していく、広告風のタワーディフェンスランナーゲームの pygame プロトタイプです。

## スクリーンショット

画像はまだありません。

```text
[ screenshot placeholder ]
```

## セットアップ方法

Python 3.11 以上、Windows 11、uv、venv を前提にしています。

```powershell
uv venv
.venv\Scripts\activate
uv sync
```

## 実行方法

```powershell
uv run python -m tower_defense_runner.main
```

または:

```powershell
uv run tower-defense-runner
```

## 操作方法

- `SPACE`: 一時停止 / 再開
- `R`: ゲームオーバー後にリスタート
- `ESC`: 終了

## ゲーム概要

- 敵は表示されたルートに沿って拠点へ進みます。
- 兵士は自動で最も近い敵、ゲート、武器コンテナを撃ちます。
- `+5`、`+10`、`x2` などのゲートを破壊すると兵士数が増えます。
- 武器コンテナを破壊すると武器レベルが上がり、攻撃力、連射速度、弾速が強化されます。
- 5 ウェーブごとに高 HP のボスが出現します。
- 敵やボスが拠点に到達すると拠点 HP が減り、0 になるとゲームオーバーです。

## ディレクトリ構成

```text
tower_defense_runner/
├─ pyproject.toml
├─ README.md
├─ LICENSE
├─ .gitignore
├─ src/
│  └─ tower_defense_runner/
│     ├─ __init__.py
│     ├─ main.py
│     ├─ settings.py
│     ├─ game.py
│     ├─ entities.py
│     ├─ weapons.py
│     ├─ waves.py
│     └─ ui.py
└─ tests/
   └─ test_basic.py
```

## 今後追加したい機能

- 敵の種類追加
- 武器の種類追加
- ゲート効果の種類追加
- ステージ追加
- セーブデータ
- サウンド
- パーティクル演出
- メニュー画面
- スマホ風 UI

## Credits

Developer: SioComb

Developed with: Codex / ChatGPT 5.5

License: CC0-1.0
