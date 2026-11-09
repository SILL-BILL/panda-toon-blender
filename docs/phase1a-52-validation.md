# Phase 1A の隔離検証と Blender 5.2.3 LTS 移行

## 5.2.3 LTS 検証結果

Blender 5.2.3 LTS、build `e13b728c6880`（`blender-v5.2-release`、2026-10-22 01:37:16）で構造・回帰テスト、3段階陰影の描画6枚、シーンの保存・再読込が成功した。最初の画像はユーザーが目視確認済み。5.1.1 の比較基準は [WIP 引き継ぎ資料](handoff-2026-11-04.md) に保持する。

隔離環境の一回の試行では Panda Toon 0.1.0 の新規インストールと別プロセス再起動が成功し、ZIPと配置済み12ファイルの一致、Extensionの有効状態、マテリアル生成と設定更新を確認した。別の新規UUIDでは、展開先 `panda_toon@` から `panda_toon` への改名が `WinError 5` で失敗した。改名を拒否した根本原因は未確定。

GUI単独再検証は、インストール・再起動に成功した環境で実施した。検証シーンのコピーを読み込み、球の選択と表示準備まで成功した。このGUI起動ではインストールを行っていない。専用設定のハッシュは起動前後で一致した。各パラメーターの手動操作確認とPhase 1A正式完了は承認待ち。

保存時の同梱ブラシ相対パス警告と、検証コードの `World.use_nodes` 非推奨警告を確認した。検証ログ上で両警告は描画と再読込を妨げなかった。LabのZIP・ログ・画像・シーン・設定はGitに含めない。

## 次工程候補

**Shadow Edge Softness** の要望を記録する。3段階の影の境界をどの程度なだらかにするか調整できるようにしたい。現在のくっきりした境界を維持できることを検討条件とし、対象とする境界、既定値、調整幅、既存マテリアルとの互換性は設計時に決める。実装は未着手。

## 実行コマンドと停止条件

承認後、リポジトリ直下の PowerShell で実行する。各行は前段のログと出力をレビューしてから個別に実行する。連続実行しない。

```powershell
$ptRunId = [guid]::NewGuid()
.\tools\run_blender_tests.ps1 -RunId $ptRunId -ExpectedVersion 5.2.3 -Stage prepare
.\tools\run_blender_tests.ps1 -RunId $ptRunId -ExpectedVersion 5.2.3 -Stage structure
.\tools\run_blender_tests.ps1 -RunId $ptRunId -ExpectedVersion 5.2.3 -Stage first
.\tools\run_blender_tests.ps1 -RunId $ptRunId -ExpectedVersion 5.2.3 -Stage remaining
.\tools\run_blender_tests.ps1 -RunId $ptRunId -ExpectedVersion 5.2.3 -Stage save
.\tools\run_blender_tests.ps1 -RunId $ptRunId -ExpectedVersion 5.2.3 -Stage install
.\tools\run_blender_tests.ps1 -RunId $ptRunId -ExpectedVersion 5.2.3 -Stage restart
.\tools\run_blender_tests.ps1 -RunId $ptRunId -ExpectedVersion 5.2.3 -Stage gui
```

- **prepare** はシステム Python の標準ライブラリで検証用 ZIP を作る。以後は同じ UUID とパッチ番号を使う。5.1.1 で同じ試験を行う場合は別承認と別 UUID が必要。
- **structure** は登録・解除・再登録と既存回帰テストを行う。実バージョンが指定したパッチ番号と一致することを確認し、ビルドハッシュ、ブランチ、日時を記録する。以後のプロセスも同一ビルドか照合する。
- **first / remaining / save** は同じ試験場面を再構成する。最初の画像を確認してから残り5枚に進む。save は最終設定で別名保存し、スクリプト実行を無効にして再読込する。
- **install** は ZIP 内のファイル名と内容を現行ソースおよびライセンスと照合する。ローカル Repository に配置し、manifest を含む全ファイル、完全修飾モジュール名、有効状態、UI 登録、マテリアル生成を確認してから専用設定を保存する。
- **restart** は別 PID で専用設定を読み込み、再インストールや再有効化を行わず、保存シーン、UI 契約、生成と設定更新を確認する。
- **gui** は比較シーンを新規コピーし、同じ専用設定で起動する。パネルを表示して操作待ちになる。確認項目は [GUI チェックリスト](phase1a-gui-closeout-preparation.md) の手動操作項目を使う。旧起動コマンドは使用対象外。手動結果と任意のスクリーンショットは UUID 内の logs に記録する。
- **gui-retry** は別承認のGUI単独再検証用。成功済みの restart を前提に、別名のシーンコピーとログを作り、同じインストール済み環境を開く。

Blender 呼び出しの形式は下記。ランチャーが絶対パスを組み立てる。structure から save は phase1a.py、install 以降は verify_install.py を指定する。

```text
blender.exe --offline-mode --disable-autoexec [--background] [--factory-startup]
  --python-exit-code 1 --python <テストスクリプト> -- <Lab絶対パス> <段階> 5.2.3
```

restart と GUI の各段階は保存した設定を読むので factory startup を外す。GUI のみ background を外す。前段の完了ファイル、終了コード、Python の成功報告を確認し、固定秒数の待機は使わない。新規例外、異常な警告、想定外の読み書きがあれば停止。ログの自動検査は既知の異常パターンに限るため、各段階で出力とファイルアクセスを確認する。途中失敗した UUID は調査用に保持する。

## 描画の比較

5.1.1 の成功条件を維持する。512 × 512 PNG、EEVEE、Standard / Look None / Exposure 0 / Gamma 1、背景強度 0、Sun 強度 3 / 角度 1°、正投影カメラ位置 (6, -10, 7) / スケール 7。ジオメトリ、色、しきい値、チェッカー画像も共通のテストコードで定義する。

| 画像 | 比較する内容 |
| --- | --- |
| 01-base | 3ゾーンの判別と境界の位置 |
| 02-light-direction | ライトを回転したときの境界・影の移動 |
| 03-thresholds | しきい値変更による領域の変化 |
| 04-base-color | ベース色変更の反映 |
| 05-texture | パック画像の色と模様、陰影との合成 |
| 06-tone-multiplier | Mid Tone 変更が対象ゾーンの明度に反映されること |

同名の5.1.1画像を横に並べ、球と立方体の同じ位置で、ゾーン数、境界の移動方向、色と模様の再現を比較する。画素の完全一致は合格条件にしない。差分が出た場合は該当画像と位置を記録し、製品変更の判断は別に行う。

## ファイルアクセスとインストール方式

- 入力はこのリポジトリの製品ソース・LICENSE・検証コード、指定の Blender 同梱リソース、同じ UUID で生成した ZIP とシーン。業務ファイルや通常プロファイルを入力に使わない。
- 出力は `lab/temp/migration-<UUID>/` 内。ZIP はルート、画像は renders、シーンは scenes、ログと完了ファイルは logs、設定・Repository・一時ファイル・キャッシュは env に置く。
- 環境変数は起動元プロセスだけで設定・復元する。保存プレビューは NONE、設定と一時ファイルの自動保存は無効。明示的な設定保存は install の専用 CONFIG に限る。
- 環境変数では OS や GPU ドライバーのファイルアクセスまで強制できない。Lab 外への書き込み試行を検出したら中断する。これを保証する必要がある場合は OS レベルの隔離が必要。同梱ブラシの相対化警告は従来と同条件である場合に記録する。

公式 Extension CLI の `extension install-file -r <repo> -e <zip>` は有効化まで指定でき、`--no-prefs` で設定保存を抑止できる。今回は既存の5.1.1成功経路との比較を優先し、バックグラウンドから `package_install_files('EXEC_DEFAULT', ...)` を使用する。同じプロセスで Repository 作成、配置確認と設定保存を順に実施できる。CLI への切り替えは今回の検証には含めない。

[Blender 5.2 Extension CLI](https://docs.blender.org/manual/en/5.2/advanced/command_line/extension_arguments.html)
