### model

```shell
openclaw config set models.providers.volcengine '{
  "baseUrl": "https://ark.cn-beijing.volces.com/api/v3",
  "apiKey": "fab9c0ab-1870-4678-aad9-d43d239586c7",
  "api": "openai-responses",
  "models": [
    {
      "id": "doubao-seed-2-0-pro-260215",
      "name": "doubao-seed-2-0-pro-260215"
    }
  ]
}'
```

```shell
openclaw config set models.providers.deepseek '{
  "baseUrl": "https://api.deepseek.com/v1",
  "apiKey": "sk-d320e94a158b46e3b9bbe8af62a37cc1",
  "api": "openai-completions",
  "models": [
    {
      "id": "deepseek-chat",
      "name": "DeepSeek Chat (V3)"
    },
    {
      "id": "deepseek-reasoner",
      "name": "DeepSeek Reasoner (R1)"
    }
  ]
}'
```


```shell
## set default model
openclaw config set agents.defaults.model.primary "deepseek/deepseek-chat"

## set model alias
openclaw models aliases add deepseek-v3 "deepseek/deepseek-chat"
openclaw models aliases add deepseek-r1 "deepseek/deepseek-reasoner"
```



`reference`
`https://juejin.cn/post/7605419006682791978`

``