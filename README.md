# 歌曲名单查询工具

这是一个 Windows 桌面小 app，用 CSV 作为数据源，可以：

- 查询歌曲是否在名单里
- 添加新歌曲
- 选中并删除歌曲
- 保存回同一个 CSV 文件

## 直接运行

1. Windows 电脑安装 Python 3。
2. 把整个 `nocopyright_desktop_app` 文件夹复制到 Windows。
3. 双击或在命令行运行：

```bat
python app.py
```

默认读取：

```text
data\nocopyright_list.csv
```

也可以在 app 里点“选择 CSV”打开其它 CSV。

## 打包成 exe

在 Windows 上双击：

```text
build_windows.bat
```

打包完成后，EXE 会在：

```text
dist\SongListApp\SongListApp.exe
```

## 用 GitHub Actions 自动打包 exe

1. 新建一个 GitHub 仓库。
2. 把这个文件夹里的所有文件上传到仓库根目录，包括隐藏目录 `.github`。
3. 打开 GitHub 仓库页面，进入 `Actions`。
4. 选择 `Build Windows EXE`。
5. 点击 `Run workflow`。
6. 运行完成后，在页面底部 `Artifacts` 下载 `SongListApp-windows`。

下载解压后，运行：

```text
SongListApp.exe
```

## CSV 格式

推荐前三列为：

```text
歌曲名,演唱,专辑
```

你的原始 CSV 前面有一行空行，app 会自动识别 `歌曲名` 这一行作为表头。
