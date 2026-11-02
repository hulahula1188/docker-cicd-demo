# 1) 基础镜像：官方 Python，alpine 版本体积只有几十 MB
FROM python:3.13-alpine

# 2) 容器内的工作目录，后续命令都在这里执行
WORKDIR /app

# 3) 先拷依赖清单再装依赖（本项目零依赖，这步先省略；有 requirements.txt 时写在这之前）
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# 4) 拷业务代码。放在依赖安装之后，改代码不会导致依赖重装，构建更快
COPY app.py .

# 5) 声明服务端口（只是文档作用，实际还需 -p 映射）
EXPOSE 8000

# 6) 容器启动命令
CMD ["python", "app.py"]
