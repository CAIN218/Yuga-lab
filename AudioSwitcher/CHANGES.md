# SoundVolumeView.exe 依存の撤廃

## 変更点

- `lib/SoundVolumeView.exe` への依存を廃止し、Windows Core Audio API を直接呼び出す
  `pycaw` ライブラリで完結するようにしました。
- `subprocess.run([EXE_PATH, "/stab", ...])` によるデバイス一覧取得
  → `AudioUtilities.GetAllDevices()` に置き換え
- `subprocess.run([EXE_PATH, "/SetDefault", ...])` による既定デバイス変更
  → `AudioUtilities.SetDefaultDevice()` に置き換え
  （内部で Windows の未公開COMインターフェース `IPolicyConfig` を呼び出し、
  Console / Multimedia / Communications の全ロールに対して既定デバイスを設定します。
  SoundVolumeView の `/SetDefault <id> all` と等価です）
- `keyboard` フックは別スレッドで発火するため、スレッドごとにCOMを初期化する
  `ensure_com_initialized()` を追加しています（pycaw/comtypes利用時の定石）。
- `lib/` フォルダ、`temp.txt`（一時ファイル）は不要になったため削除しました。

## セットアップ

```
pip install -r requirements.txt
```

## 実行・ビルド

これまで通りです。

```
python switch_audio.py
```

exe化する場合:

```
pyinstaller AudioSwitcher.spec
```

`pycaw` / `comtypes` はPyInstallerが動的インポートを検出しづらいことがあるため、
`AudioSwitcher.spec` の `hiddenimports` に明示しています。ビルド後に一度アプリを
起動してデバイス切り替えが正常に動くか確認してください（うまく動かない場合は
`hiddenimports` に `comtypes.gen` を追加するか、`--collect-all pycaw` を試してください）。

## 注意点

- `IPolicyConfig` はMicrosoft非公開のCOMインターフェースです（Windows 7以降で
  広く使われている枯れた手法ですが、将来のWindows更新で挙動が変わる可能性はゼロではありません）。
- 管理者権限は基本的に不要です。
