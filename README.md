# 最小可跑的 Docker + CI/CD 案例

一个零依赖的 Python 小服务，用来把 Docker 和 CI/CD 从头跑一遍。全部命令都在本目录下执行。

```
docker-cicd-demo/
├── app.py                      # 服务本体（只用标准库）
├── test_app.py                 # 4 个测试（2 个单元 + 2 个真实 HTTP 请求）
├── Dockerfile                  # 打包配方
├── .dockerignore               # 哪些文件不用塞进镜像
└── .github/workflows/ci.yml    # GitHub Actions 流水线
```

---

## 第 0 步：装 Docker（macOS 只做一次）

推荐 Docker Desktop：

```bash
brew install --cask docker
open -a Docker          # 启动后等鲸鱼图标变绿
docker version          # 能看到 Client 和 Server 两段才算成功
```

装完先来个经典验证：

```bash
docker run --rm hello-world
```

---

## 第 1 步：不装 Docker 也能先跑通代码

```bash
cd docker-cicd-demo
python3 -m unittest -v test_app          # 应看到 4 个 ok
python3 app.py                            # 另开一个终端
curl "http://localhost:8000/hello?name=你"
```

---

## 第 2 步：构建镜像

```bash
docker build -t demo:v1 .
```

- `-t demo:v1` = 起名字叫 demo，版本 v1
- 末尾的 `.` = 把当前目录当构建上下文发给 Docker，**别漏**

看镜像列表和体积：

```bash
docker images | grep demo
```

第一次跑大概十几秒到一分钟（要下载 python:3.13-alpine 基础镜像），之后有缓存会快很多。

---

## 第 3 步：跑起来

```bash
docker run -d --name demo -p 8000:8000 demo:v1
curl http://localhost:8000/health
curl "http://localhost:8000/hello?name=Docker"
```

- `-d` 后台运行
- `-p 8000:8000` = 宿主机端口:容器端口
- `--name demo` 起个容器名，方便后面操作

常用运维命令：

```bash
docker ps                # 在跑的容器
docker logs -f demo      # 实时看日志
docker stats demo        # 看 CPU / 内存
docker exec -it demo sh  # 进容器内部逛逛
docker rm -f demo        # 停掉并删除
```

---

## 第 4 步：体验"环境一致"到底是什么意思

改一行 `app.py` 里的问候语，然后：

```bash
docker build -t demo:v2 .
docker rm -f demo
docker run -d --name demo -p 8000:8000 demo:v2
```

新版本照样跑起来，不需要在服务器上装 Python、配环境变量。这就是容器解决的核心痛点。

**感受一下分层缓存**：只改 `app.py` 时，`COPY app.py .` 之前的所有层都命中缓存，构建几乎瞬间完成。这也是为什么 Dockerfile 里要把"装依赖"写在"拷代码"之前。

---

## 第 5 步：接入 CI/CD

### 5.1 推到 GitHub

```bash
git init
git add .
git commit -m "feat: docker + ci demo"
git branch -M main
git remote add origin git@github.com:<你的用户名>/docker-cicd-demo.git
git push -u origin main
```

仓库在 GitHub 上先手动建一个空的（不要勾选 README）。

### 5.2 流水线自动触发

推送完成后打开仓库的 **Actions** 标签页，会看到一个叫 `CI/CD` 的流水线在跑，9 个步骤依次点亮：

| 步骤 | 在干什么 |
|---|---|
| 1-2 | 拉代码、装 Python |
| 3 | 跑单元测试（挂了就红，后面全不执行） |
| 4 | 构建镜像 |
| 5 | 起容器 + curl `/health` 冒烟测试 |
| 6 | 清理容器 |
| 7-9 | 只有 main 分支才执行：登录 GHCR、打标签、推镜像 |

### 5.3 看结果

跑成功后，镜像被推到了 GitHub 自带的镜像仓库：

```
ghcr.io/<你的用户名>/docker-cicd-demo:latest
```

在仓库首页右侧的 **Packages** 里能看到。任何一台装了 Docker 的机器都可以：

```bash
docker pull ghcr.io/<你的用户名>/docker-cicd-demo:latest
docker run -d -p 8000:8000 ghcr.io/<你的用户名>/docker-cicd-demo:latest
```

这一步就是 CD 的终点：**代码合并 → 自动测试 → 自动出镜像 → 任何机器一条命令拉起来**。

---

## 第 6 步：验证"坏了会被拦住"

故意把 `test_app.py` 里的期望值改错，比如 `"Hello, Docker!"` 改成 `"Hello, Docker!!"`，再 push。

结果：第 3 步测试变红，流水线中止，镜像根本不会被构建，更不会推上去。这就是 CI 的价值——**问题在合并前暴露，而不是上线后**。

---

## 常见坑

| 现象 | 原因 |
|---|---|
| `Cannot connect to the Docker daemon` | Docker Desktop 没启动 |
| `port is already allocated` | 8000 被占用，换 `-p 8001:8000` |
| 容器起来就退出 | `docker logs demo` 看报错，多半是启动命令写错 |
| 宿主机 curl 不通 | 服务必须监听 `0.0.0.0`，不能是 `127.0.0.1` |
| CI 里 docker 命令找不到 | ubuntu-latest 自带 docker，若换 runner 需自己装 |
| 推 GHCR 报 denied | 仓库 Settings → Actions → General 里把 Workflow permissions 设为 Read and write |

---

## 再往下可以学什么

1. **多阶段构建**：编译环境和运行环境分开，镜像能瘦一半以上
2. **docker compose**：一个应用 + 一个数据库，一条 `docker compose up` 全起来
3. **compose/镜像里的密钥管理**：环境变量、`.env`、GitHub Secrets
4. **健康检查与重启策略**：`HEALTHCHECK`、`--restart unless-stopped`
