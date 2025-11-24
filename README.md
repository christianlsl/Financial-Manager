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

### Database

Reset and Initialize Database:

```bash
cd ./backend

# Reset database and insert sample data (default)
uv run -m app.utils.manage_db --action reset_and_seed

# Or reset database only (no sample data)
uv run -m app.utils.manage_db --action reset
```

Run development server:

```bash
uv run uvicorn app.main:app --reload --port 9910
```

API docs: http://127.0.0.1:9910/docs

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

1. 将后端文件/backend上传至服务器

2. ```bash
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
   npm run build
   ```

3. 上传./dist到服务器静态文件目录（默认：'/usr/share/nginx/html'）

   ```bash
   scp -r .\dist\* root@47.100.89.197:/usr/share/nginx/html
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
   systemctl restart nginx  # 重启服务
   # 或
   # nginx -s reload
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

   

## clean vscode server

```bash
# Kill server processes
kill -9 $(ps aux | grep vscode-server | grep $USER | grep -v grep | awk '{print $2}')
# Delete related files and folder
rm -rf $HOME/.vscode-server # Or ~/.vscode-server-insiders
```