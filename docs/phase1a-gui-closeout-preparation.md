# Phase 1A GUI検証・完了承認準備（2026-10-27）

状態：技術検証はユーザー承認済み、描画は暫定合格。手動GUI検証は未実施。
起動案を静的確認した段階であり、今回GUI起動・インストールは行っていない。

## 起動案：実行前確認対象

プロジェクトルートから：

```powershell
powershell -NoProfile -File "D:\dev-blender-addon\panda-toon-blender\lab\temp\gui-review-5e3af32eb4cb42ccbb768d838b022808\launch-gui.ps1"
```

内部コマンド：Blender 5.1.1 に --offline-mode --disable-autoexec --factory-startup
--python-exit-code 1 --python <同フォルダーのgui_setup.py> を渡す。表示用GUIなので
--background は付けない。起動案は構文確認のみで、GUIでの実行結果は未検証。

読み取り：Blender本体と同梱資源、検証済みZIPのコピー、検証シーンのコピー。
新規インストール先：同UUIDの env/BLENDER_USER_EXTENSIONS/panda_gui。
設定・スクリプト・データ・一時ファイル・ログ：同UUID内の env/ および gui.log。
通常設定の保存、設定自動保存、シーン自動保存は行わない。file_preview_type=NONE。
製品コード・既存ZIP・過去の検証結果は変更しない。

Windows/GPUの内部アクセスまで環境変数だけで隔離できるわけではない。
NONEは保存プレビューだけの抑止で、ファイルブラウザー等のキャッシュ全般は対象外。
今回は外部ファイルやAsset Browserを開かず、同梱済み画像の選択だけを行う。
新しいPythonエラー・保存先外への書き込みを検出したら操作を中断して報告する。
通常の制作ファイルは開かない。終了時はシーン変更を保存せず破棄する。
保存が必要になったら事前確認し、このUUID内の新しい名前だけを使う。

## 手動チェック（約5～10分）

起動準備スクリプトは球を選択し、EEVEEのRendered表示とMaterial Propertiesを開く。
初回のシェーダーコンパイル完了を待つ。必要ならテンキー0でカメラ表示にする。

| 操作 | 期待結果 |
|---|---|
| Preferences > Add-onsでPanda Toonを検索（状態を見るだけ） | 有効。バージョン0.1.0 |
| 選択した球のMaterial Propertiesを確認 | Panda Toon Materialパネル、ボタン、7設定項目が表示。欠けや重なりなし |
| New Panda Toon Materialをクリック | 新しいスロットが追加され、選択状態になる。既存スロットは残る |
| 球をEdit ModeにしてAで全選択、追加スロットのAssignを押してObject Modeへ戻る | 球の面に新しいマテリアルが割り当てられる。生成ボタンは既存面の割当を自動置換しない仕様 |
| Base Colorを青→赤などへ変更 | 表示色が変わり、陰影段階は残る |
| Base Color Textureの画像一覧からPT_Checkerを選択 | 模様とBase Colorと陰影が合成される。×で解除すると単色へ戻る。外部画像のOpenは不要 |
| Threshold 1を0.25→0.4、Threshold 2を0.65→0.8へ変更 | 陰影境界・各ゾーンの面積が変化。逆転方向に動かすと相手の値で止まる |
| Lightを1→0.8、Midを0.55→0.7、Darkを0.2→0.1へ一つずつ変更 | 対応ゾーンの明度が変わる。境界位置は基本的に維持 |
| 一連の操作とパネル表示を確認 | Pythonエラーなし、値が反映され、UI崩れなし |

画像選択では8x8のテスト画像に線形補間がかかるため、模様はぼけた表示になる。
エラーが出たら何を操作したかとメッセージを記録し、その先へ進めない。

## スクリーンショットと結果記入

OSのスクリーンショットで以下を保存する場合、同UUID内の新しい名前を使う。
1. 01-addon-enabled.png：有効状態とバージョン。
2. 02-material-panel.png：生成後のスロット、パネル全体とRenderedの球。
3. 03-color-thresholds.png：色・しきい値変更後、数値と表示を同時に収める。
4. 04-texture-tones.png：テクスチャ・倍率変更後、数値と表示を同時に収める。
失敗時は追加でエラー画面を保存。これらは未取得であり、CLI画像で代用しない。

結果：各行について OK / NG / 未確認、エラー文、再現操作をユーザーが回答する。
全項目OKになるまでGUI合格・正式完了とは記録しない。

## ブラシ警告の分類（読み取り調査）

ログは保存時に、C:/Program Files/Blender Foundation/Blender 5.1/5.1/datafiles/assets/
brushes/essentials_brushes-gp_draw.blend を Material 'Dots Stroke' と 'Material' に
対して相対化できなかったと報告している。保存先はD:ドライブ。

Blender v5.1.1のbpath.cc relative_convert_foreach_path_cbに同一の警告文があり、
相対化に失敗すると警告して元のパスを保持する。弱いライブラリ参照も巡回対象になる。
ドライブをまたぐ保存先が直接の条件と判断できる。初期シーンに同梱ブラシ由来の
参照が残っていることが示唆されるが、今回そのデータブロックを実行調査してはいない。

- 警告の発行元：Blender本体のパス変換処理。
- 対象：検証シーンに含まれる同梱ブラシ由来の参照。Panda Toonノードではない。
- Panda Toonソース：ブラシ読込・パス相対化の処理は存在しない。
- ZIP：Python、manifest、説明、LICENSEの12ファイルのみ。ブラシやblendは含まない。
- 確認済み影響：ZIP検証・インストール・別プロセス読込・保存再読込に失敗なし。
- 留保：別PCへ検証blendを移動した際のブラシ参照の可搬性までは保証しない。
- 対応：製品修正不要と判断。警告を消す目的のデータ削除や無断変更は行わない。
  必要なら、後でテスト用保存のパス再配置設定を限定的に見直す案をレビューする。

根拠：
https://github.com/blender/blender/blob/v5.1.1/source/blender/blenkernel/intern/bpath.cc#L483
https://github.com/blender/blender/blob/v5.1.1/source/blender/blenkernel/intern/bpath.cc#L84
ログ：lab/temp/install-66bba68eea0e4f1faf30ea768202f5a5/install.log

## ZIPとソースの対応

検証済みZIPは上記install UUIDの panda_toon-0.1.0-current.zip。
GUI用ZIPはそのバイト同一コピーで、再ビルドはしていない。
2026-10-27に全12エントリーと最新src/およびLICENSEの一致を再確認。
SHA-256: 3fa5a09c252a52f5e334bbad122b3d3f6773471a1b6a52ea2cc242b1f1e34db8

## Git・除外確認・Commit準備

既存追跡ファイルの変更：LICENSE、README.md。
新規候補：.gitignore、AGENTS.md、docs/、src/panda_toon/、tests/、tools/。
今回の追加は本準備文書とlab/temp内の準備資料のみ。製品ソースは変更なし。
候補の全ファイル名はGUI用UUID内 commit-candidates-current.txt に記録する。
Git add/commit/pushは行っていない。

.gitignore実測：dist/*、lab/temp/*、lab/logs/*、lab/renders/*は除外。
__pycache__、pyc、一時設定、blendバックアップも除外。
tests/baselines/*、lab/scenes/*は除外されないため、将来の追加時は個別レビューが必要。
ZIP・専用userpref・キャッシュ・生ログ・今回のスクリーンショットはCommit対象外。

Commit前の要整理事項（未変更・提案）：
- AGENTS.md末尾の古い実行承認状態は、現時点の工程別承認を正しく表すよう整理する。
- READMEとdocsの未検証表記・テスト件数・工程状態を実績に合わせる。
- 通常のtests/blender/phase1a.pyとtools/run_blender_tests.ps1にはNONE設定等の
  後続検証済み手順が未統合。現状の古い手順を最新版として再実行しない。
- 検証済みの安全措置・インストール/再起動手順を標準テストへ統合する案を提示し、
  承認後に変更・必要な検証を行う。成功版の実行スクリプトは現在ignoredのLab内。
- GUI結果と警告分類を正式報告へ反映し、レビュー用証跡の要約をdocsに残す。

現在の候補一覧はそのままCommitしてよいという意味ではない。
GUI合格と上記整理のレビュー後に正式完了・Commitを判断し、Pushは別承認とする。
