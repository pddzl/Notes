IP: 172.20.1.22

`systemctl --user start openclaw-gateway`

`nginx`

```shell
server {
	listen 443 ssl;
    server_name openclaw.trinasolar.com;
    
    ssl_certificate /etc/nginx/ssl/server.crt;
    ssl_certificate_key /etc/nginx/ssl/server.key;
    
    location / {
        auth_basic "Restricted Area";
        auth_basic_user_file /etc/nginx/.htpasswd;
        proxy_pass http://127.0.0.1:18789;

        # 传递真实IP
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 延长超时时间 防止长任务中断
        proxy_read_timeout 300s;
    }
}
```

`user/passwd`

`openclaw-sre\openclaw-trina`

`reference`

`https://cloud.tencent.com/developer/article/2634692?policyId=1004`