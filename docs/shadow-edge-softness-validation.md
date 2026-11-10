# Shadow Edge Softness 試作の隔離検証

新規 Panda Toon マテリアルは schema 2。Material Properties のスライダーは既定値 0.00、範囲 0.00–1.00。幅 0.00 は従来の厳密な `LESS_THAN` マスクを使う。正の値は各しきい値を中心とする明度幅として扱い、両境界に同じ幅の Smooth Step を適用する。schema 1 は従来のグラフと設定項目を使い、自動移行は行わない。

## 検証結果（2026-11-10）

- Blender 5.2.3 LTS（build `e13b728c6880`）で承認済みの4段階が終了コード 0。schema 1 の更新、同一グラフの繰り返し更新、schema 2 の Softness 0.15 の保存・再読込に成功。
- 同一条件の 512 × 512 EEVEE PNG 5枚を生成。schema 1 と schema 2 の 0.00 は全 262,144 画素で一致。schema 1 との差分は 0.05 で 4,699 画素、0.15 で 16,343 画素、0.30 で 29,282 画素。
- ゴン作が GUI で操作し、見た目と操作感を確認して試作を目視合格とした。GUI の JSON にある `manual_result=pending` は起動時点の記録。終了ログは `Blender quit`、完了マーカーあり。Blender は終了時のセッション復旧ファイルを今回の隔離先 `env/TEMP/quit.blend` に作成した。
- 描画時に既知の `World.use_nodes` 非推奨警告、保存時に Blender 同梱ブラシのパスを相対化できない警告が出た。
- 5.2.3 での Extension 新規インストール時の `WinError 5` は未解決。今回は現行ソースをプロセス内で登録して検証した。正式採用、Phase 1A の正式完了、Release は保留。

## 実行承認の対象

リポジトリ直下 `D:\dev-blender-addon\panda-toon-blender` の PowerShell で、各段階の終了コードとログを確認してから次の行を実行する。

```powershell
$ptRunId = '69670628-5217-45db-8904-ea6d211222e5'
.\tools\run_blender_tests.ps1 -RunId $ptRunId -ExpectedVersion 5.2.3 -Stage prepare
.\tools\run_blender_tests.ps1 -RunId $ptRunId -ExpectedVersion 5.2.3 -Stage structure
.\tools\run_blender_tests.ps1 -RunId $ptRunId -ExpectedVersion 5.2.3 -Stage softness
.\tools\run_blender_tests.ps1 -RunId $ptRunId -ExpectedVersion 5.2.3 -Stage softness-gui
```

- `prepare` はシステム Python で現行ソース・LICENSE を検証用 ZIP にまとめ、専用ディレクトリを作る。ZIP は検証ランチャーの準備成果物として保持する。
- `structure` と `softness` は `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe` を `--offline-mode --disable-autoexec --background --factory-startup --python-exit-code 1` で起動する。Python エントリは [phase1a.py](../tests/blender/phase1a.py)。構造検証は [initialization_checks.py](../tests/blender/initialization_checks.py) も使用する。実行中のバージョンを 5.2.3 に照合し、後続の段階は構造検証と同じビルドであることを確認する。
- `softness-gui` は `--background` を外し、同じ実行ファイルとスクリプトで新規シーンコピーを開く。球を選択し、Material Properties とレンダー表示を用意する。合否はゴン作の手動操作で判断する。
- Blender の入力は同梱リソース、リポジトリの試作ソース・検証コード（[lab_support.py](../tests/blender/lab_support.py) を含む）、この検証内で新規生成したシーンと画像。現行ソースをプロセス内で登録し、Extension のインストールや設定保存は行わない。

## 出力と停止条件

出力は `lab/temp/migration-69670628521745db8904ea6d211222e5/` の新規ディレクトリ内に作る。

- `renders/` に `schema1-hard-reference.png` と `softness-0.00.png`、`softness-0.05.png`、`softness-0.15.png`、`softness-0.30.png`。同一の球、照明、カメラ、色管理、512 × 512 EEVEE 設定で描画し、旧描画と 0.00 の画像の画素値を比較する。
- `scenes/` に保存・再読込用 `softness.blend`（幅 0.15）と、GUI 用 `softness-review.blend`。
- `logs/` にステージごとのログ、JSON、完了マーカー。`env/` に隔離設定、一時ファイル、キャッシュ用ディレクトリ。ルートに準備用 `panda_toon.zip`。

既存出力、リパースポイント、バージョン不一致、実行エラー、想定外の診断やファイルアクセスを検出した場合は停止する。設定と一時ファイルの自動保存は無効にする。OS や GPU ドライバーが隔離先の外へキャッシュを書き込む可能性は残る。
