# 复现步骤

> 全程只读 + 最后的卸载动作可逆。需要 root（读取 `/data/data`）。

## 0. 前置

```bash
adb devices
adb shell getprop ro.build.display.id      # 记录版本
adb shell pm list packages | grep -E "regservice|ctautoregist"
```

## 1. 组件与权限

```bash
adb shell dumpsys package com.coloros.regservice | grep -E "codePath|versionName|flags=|targetSdk"
adb shell dumpsys package com.coloros.regservice | grep "granted=true" | wc -l
adb shell dumpsys package com.coloros.regservice | grep -c "android.intent.category.LAUNCHER"   # 0
```

## 2. 取出数据库

```bash
adb shell su -c 'cp /data/data/com.coloros.regservice/databases/cmcc_dm.db /sdcard/Download/'
adb pull /sdcard/Download/cmcc_dm.db .
python3 scripts/inspect_db.py cmcc_dm.db
```

`inspect_db.py` 只输出表名、行数、字段名与脱敏样本，不会打印个人数据。

## 3. 观察定时任务

```bash
adb shell dumpsys alarm | grep -B2 -A6 com.coloros.regservice
```

## 4. 触发一次上报（可选）

```bash
adb shell am broadcast -a cn.richinfo.dmyk.action.HEARTBEAT \
  -n com.coloros.regservice/com.dmyk.android.telephony.OppoReceiver
```

同时抓包：

```bash
adb shell su -c 'tcpdump -i any -n -s0 -X "host 117.134.71.39 and tcp port 443"'
```

观察点：

1. 抓包出现 `a.fxltsbl.com` 的 SNI；
2. `logcat | grep RegService_` 出现 `"status":"report","result":1`；
3. 再次导出数据库，对比行数变化（上报成功后对应表应为 0 行）。

> 若网络被认证网关劫持，会看到自签证书 + `TLS Alert 0x2e`，属预期现象。

## 5. 处置

```bash
adb shell pm uninstall --user 0 com.coloros.regservice
adb shell pm uninstall --user 0 com.oppo.ctautoregist
adb shell cmd package install-existing com.coloros.regservice   # 恢复
```

## 6. 自查其他同类组件

```bash
# 运营商 DM 类
adb shell pm list packages | grep -iE "register|autoreg|dm\\.|richinfo|systemhelper"
# 可疑的默认授予特权的预装应用
adb shell dumpsys package <pkg> | grep -E "READ_PRIVILEGED_PHONE_STATE|QUERY_ALL_PACKAGES"
```
