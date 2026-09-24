
| 指标                                | 含义                                            | 说明                         |
| --------------------------------- | --------------------------------------------- | -------------------------- |
| **TTFB**（Time to First Byte）      | 从发出请求到收到**第一个字节**的时间，反映后端响应速度                 |                            |
| Value A                           | Value B                                       |                            |
| **DCL**（DOMContentLoaded）         | DOM 树构建完成（不等图片等资源），对应 `DOMContentLoaded` 事件   |                            |
| **FCP**（First Contentful Paint）   | 首次内容渲染，如首段文本或图片                               |                            |
| **LCP**（Largest Contentful Paint） | 页面中**最大内容元素**渲染完成时间，影响用户对加载完成的感知              |                            |
| LoadEventEnd                      | `window.onload` 事件完成时间，表示所有资源加载完（包括图片、iframe） | 不用于关键性能评估，但时间过长说明资源多或加载慢   |
| 完全加载                              | 页面所有资源加载完成所用总时间                               | 与 LoadEventEnd 相近，说明加载没有卡顿 |
| 资源错误数                             | 加载失败的图片、脚本、字体等数量                              |                            |

```shell
|---TTFB---|-------FCP------|----DCL----|----------LCP----------|------onload------|
    ↓          ↓               ↓             ↓                     ↓
请求发出   首次渲染     DOM构建完成     最大内容渲染       所有资源加载完

```

| 类别                      | 含义                                       |
| ----------------------- | ---------------------------------------- |
| resource.script         | 加载 JS 脚本所耗时间（包括 `.js` 文件、内联脚本等）          |
| resource.link           | 加载 HTML 中的 `<link>` 资源，通常是外部 CSS 文件      |
| navigation              | 从点击链接到接收到首字节（TTFB），即页面导航和响应等待时间          |
| resource.xmlhttprequest | 异步请求的加载时间（如 Ajax 请求）                     |
| resource.css            | CSS 样式表的加载（部分浏览器会将 `.css` 和 `link` 区分统计） |
| resource.fetch          | 使用 `fetch()` API 请求资源的耗时（如动态数据、图片等）      |
