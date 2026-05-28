# Financial Manager

FastAPI + Vue3 financial management system for small companies. Features:

- Email registration and login with JWT authentication and RSA encryption
- Manage purchase list, sales list, and invoices
- SQLite storage (default) with SQLAlchemy ORM


## Backend

Install dependencies (using uv or pip):

```bash
uv sync
```

### RSA Key Initialization

The system uses RSA encryption for password security. Initialize the encryption keys:

```bash
cd ./backend

# Generate RSA key pair for password encryption
uv run app/utils/init_keys.py
```
修改config_example.yaml为config.yaml并增加配置

### Database

Reset and Initialize Database:

```bash
cd ./backend

# Reset database and insert sample data (default)
uv run -m app.utils.manage_db --action reset_and_seed

# Or reset database only (no sample data)
uv run -m app.utils.manage_db --action reset
```

### Run

#### Run development server

```bash
uv run uvicorn app.main:app --reload --port 9910
```

API docs: http://127.0.0.1:9910/docs

#### Debug server

+ modify .vscode/launch.json

  ```json
  {
      "version": "0.2.0",
      "configurations": [
          {
              "name": "Python: FastAPI",
              "type": "debugpy",
              "request": "launch",
              "module": "uvicorn",
              "args": [
                  "main:app",
                  "--host",
                  "127.0.0.1",
                  "--port",
                  "9910",
                  "--reload"
              ],
              "cwd": "${workspaceFolder}/backend",
              "env": {
                  "PYTHONPATH": "${workspaceFolder}/backend"
              }, // 解决模块导入问题
              "justMyCode": false, // 允许调试第三方库（如 FastAPI/Uvicorn，可选）
              "console": "integratedTerminal"
          }
      ]
  }
  ```

+ debug button on left sidebar of vscode

### Tests

```bash
uv run pytest -q
```

## Frontend

Located in `frontend/` (Vite + Vue 3 + Pinia + Router + Axios).

Install & run:

```bash
cd frontend
npm install
npm run dev
```



#### API Configuration

The frontend is configured to use relative paths (e.g., `/api/users`) for API calls. In development mode, Vite proxy is used to forward these requests to the backend server.

**Development Environment:**
- API requests are automatically proxied to `http://127.0.0.1:9910` via Vite
- No additional configuration needed

**Production Environment:**
- If frontend and backend are served from the same domain, no configuration needed
- If served from different domains, create `.env.production` with:
  ```
  VITE_API_BASE=https://your-backend-domain.com
  ```
## Set to Production Mode

### 部署后端

1. 修改config.yaml

   ```yaml
   database:
     sqlite_db_path: /root/Financial-Manager/financial_manager.db
   ```

2. 将后端文件/backend上传至服务器

   ```bash
   scp -r ./* root@47.100.89.197:~/Financial-Manager/backend

   # scp -r ./app/* root@47.100.89.197:~/Financial-Manager/backend/app
   ```

3. ```bash
   uv sync
   ```

#### 部署系统服务

1. ```bash
   vi /etc/systemd/system/fastapi.service
   ```

2. 编辑服务文件

   ```bash
   [Unit]
   Description=FastAPI Service
   After=network.target
   
   [Service]
   User=root
   WorkingDirectory=/root/Financial-Manager/backend
   ExecStart=/root/Financial-Manager/backend/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 9910 --workers 2
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   ```

3. 保存文件并设置自启动

   ```bash
   systemctl daemon-reload  # 重新加载配置
   systemctl start fastapi  # 启动服务
   systemctl enable fastapi  # 开机自启
   ```

4. 验证后端

   服务器内执行`curl http://127.0.0.1:9910`，返回 JSON 即为成功。

### 部署前端

1. Set `VITE_API_BASE` in `.env.production` to your backend domain

2. Build frontend and deploy

   ```bash
   cd frontend
   npm run build
   ```

3. 上传./dist到服务器静态文件目录（默认：'/usr/share/nginx/html'）

   ```bash
   scp -r ./dist/* root@47.100.89.197:/usr/share/nginx/html

   # login remote server
   sudo chmod -R 755 /usr/share/nginx/html
   ```

#### 编辑nginx反向代理

1. 配置文件

   ```bash
   vi /etc/nginx/conf.d/default.conf
   ```

   ```bash
   server {
       listen 80;
       server_name 47.100.89.197;  # 替换为你的公网IP
   
       root /usr/share/nginx/html;
       index index.html;
   
       # 处理Vue路由刷新404
       location / {
           try_files $uri $uri/ /index.html;
       }
   
       # 反向代理后端API（解决跨域）
       # 说明：前端访问 /api/* 会被转发到后端 http://127.0.0.1:9910/*
       # proxy_pass 末尾的 / 会去掉 /api 前缀，后端实际路由不包含 /api
       location /api/ {
           proxy_pass http://127.0.0.1:9910/;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

2. 检查配置并重启

   ```bash
   nginx -t  # 验证配置是否正确
   nginx -s reload
   systemctl restart nginx  # 重启服务
   ```

### 测试与排查

1. **访问项目**

   本地浏览器输入ip，查看前端页面是否正常加载，后端接口是否可调用。

2. **前端空白**

   + 为静态文件授予权限

     ```bash
      sudo chmod -R 755 /usr/share/nginx/html
     ```

   + 保证vit.config.js中的` base: '/'`和nginx的`location / {...}`一致，都是 **/**，或其他自定义位置

3. **后端接口不通**

   + 查看服务状态

     ```bash
     systemctl status fastapi
     ```

   + 查看日志

     ```bash
     journalctl -u fastapi -f
     ```

   + 假装前端ping后端

     ```bash
     curl http://47.100.89.197/api/auth/pubkey
     ```

4. **跨域错误**
   + 保证前端`base_url`和nginx的后端反向代理`location /api/`保持一致



### 更新文件/配置

1. 重新上传文件

2. 重启

   ```bash
   systemctl restart fastapi
   nginx -t
   systemctl restart nginx
   ```

   

## Docker 部署（fnos 等 NAS 环境）

### 前置准备

1. 本地构建前端

   ```bash
   cd frontend
   npm run build
   ```

2. 准备 `backend/config.yaml`，修改数据库路径：

   ```yaml
   database:
     sqlite_db_path: ./backend/data/financial_manager.db
   ```

   > 路径相对于项目根目录（容器内 `repo_root` = `/app`），必须包含 `./backend/` 前缀。

### 构建并导出后端镜像

```bash
docker compose build backend
docker save financial-manager-backend | gzip > backend-image.tar.gz
```

> nginx 使用官方 `nginx:alpine` 镜像，无需构建和导出，fnos 会自动拉取。

### 部署到 fnos

1. **上传文件到 fnos**

   将以下文件传到 fnos 上同一目录：

   ```
   <部署目录>/
   ├── docker-compose.yml
   ├── Dockerfile
   ├── backend-image.tar.gz
   ├── backend/
   │   └── config.yaml
   ├── frontend/
   │   └── dist/          ← 已构建的前端产物
   ├── nginx/
   │   └── nginx.conf
   └── data/
       └── financial_manager.db   ← 数据库文件
   ```

2. **导入后端镜像**

   ```bash
   docker load < backend-image.tar.gz
   ```

3. **启动服务**

   ```bash
   docker compose up -d
   ```

   nginx 会自动从 Docker Hub 拉取 `nginx:alpine`。

4. **验证**

   访问 `http://<fnos-ip>:5678` 查看前端页面，访问 `http://<fnos-ip>:5678/api/docs` 查看 API 文档。

### 更新部署

- **更新前端**：重新 `npm run build`，替换 `frontend/dist/`，执行 `docker compose restart nginx`
- **更新后端**：重新构建镜像并替换，执行 `docker compose up -d`
- **更新数据库**：替换 `data/financial_manager.db`，执行 `docker compose restart backend`

### 注意事项

1. **`config.yaml` 中数据库路径**

   代码中 `repo_root` 取的是 `config.py` 向上 3 级目录，容器内解析为 `/app`。因此相对路径必须从项目根算起：

   ```yaml
   # 正确
   sqlite_db_path: ./backend/data/financial_manager.db
   # 错误（会解析为 /app/data/...，文件不存在）
   sqlite_db_path: ./data/financial_manager.db
   ```

2. **前端静态文件权限**

   `frontend/dist` 以只读卷挂载进 nginx 容器，容器内 nginx 用户（UID 101）需要有读取权限。部署后执行：

   ```bash
   chmod -R 755 frontend/dist
   ```

3. **数据库目录权限**

   SQLite 需要对数据库所在 **目录** 有写权限（用于创建 journal/WAL 文件）。确保 `data/` 目录可写：

   ```bash
   chmod 755 data/
   ```

## clean vscode server

```bash
# Kill server processes
kill -9 $(ps aux | grep vscode-server | grep $USER | grep -v grep | awk '{print $2}')
# Delete related files and folder
rm -rf $HOME/.vscode-server # Or ~/.vscode-server-insiders
```