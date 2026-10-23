# 第三方资源核查

本项目实际页面仅引用自有 `app/static/css/app.css`、自有图表初始化脚本及本地Chart.js，未引入Bootstrap，没有其文件、CDN引用或需要随包携带的Bootstrap许可证。不能把早期建议写成已经使用。

| 随项目分发的第三方资源 | 版本/来源 | 许可证及实际核查 |
|---|---|---|
| Chart.js UMD及source map | 4.5.1，官方npm分发包；来源详vendor/README.md | MIT，完整许可证保留在app/static/vendor/Chart.js-LICENSE.md；文件存在、模板同源引用、HTTP200、浏览器两图实际绘制 |

Chart.js UMD的SHA256为 `48444a82d4edcb5bec0f1965faacdde18d9c17db3063d042abada2f705c9f54a`。Phase4已核对下载tarball的npm SHA512 integrity；Phase5重新核对本地文件SHA256。source map也来自同包，不含本机账号、密钥或个人绝对路径。

Python依赖由pip根据requirements安装，最终源码包不复制虚拟环境或把这些库当作自有源代码。干净环境实际版本和包许可证元数据保存在 `ai_evidence/phase5/versions.txt`、`python_licenses.txt`；元数据缺失字段按null保留，不臆造许可证结论。若将来额外分发依赖二进制/安装包，应随其实际分发条款保留对应声明；本轮未打包依赖安装包。

离线运行所需的页面CSS和图表JS已在源码中；首次pip安装仍需要包源联网。真实断外网后浏览器重载未执行，不把本地文件存在当作已完成该人工项目。
