screen=Insert(document, {type: "frame", name: "聊天页面UI设计", layout: "horizontal", width: 1440, height: "fit_content(900)", fill: "#f8fafc", placeholder: true})

sidebar=Insert(screen, {type: "frame", name: "Sidebar", layout: "vertical", width: 260, height: 900, fill: {type: "gradient", from: "#667eea", to: "#764ba2", angle: 180}, padding: 0})

logoArea=Insert(sidebar, {type: "frame", name: "Logo区域", layout: "horizontal", width: 260, height: 72, gap: 12, alignItems: "center", padding: [16, 20]})
logoIcon=Insert(logoArea, {type: "ellipse", name: "Logo图标", width: 40, height: 40, fill: "rgba(255,255,255,0.25)", stroke: "rgba(255,255,255,0.4)", strokeWidth: 2})
logoText=Insert(logoArea, {type: "text", content: "AI 聊天助手", fontSize: 18, fontWeight: 600, fill: "#ffffff", fontFamily: "$--font-primary"})

newConvBtn=Insert(sidebar, {type: "rectangle", name: "新建对话按钮", width: 228, height: 48, x: 16, y: 88, fill: "rgba(255,255,255,0.25)", stroke: "rgba(255,255,255,0.4)", strokeWidth: 1, cornerRadius: 12})
newConvText=Insert(newConvBtn, {type: "text", content: "+ 新建对话", fontSize: 14, fontWeight: 500, fill: "#ffffff", fontFamily: "$--font-primary"})

convList=Insert(sidebar, {type: "frame", name: "会话列表", layout: "vertical", width: 228, x: 16, y: 152, gap: 8})

conv1=Insert(convList, {type: "rectangle", name: "会话项1", width: 228, height: 72, fill: "rgba(255,255,255,0.2)", cornerRadius: 12})
conv1Icon=Insert(conv1, {type: "ellipse", name: "会话图标", x: 12, y: 16, width: 40, height: 40, fill: "rgba(255,255,255,0.3)"})
conv1Title=Insert(conv1, {type: "text", content: "Python排序算法", x: 64, y: 16, width: 140, height: 20, fontSize: 14, fontWeight: 500, fill: "#ffffff", fontFamily: "$--font-primary"})
conv1Preview=Insert(conv1, {type: "text", content: "帮我写一个快速排序...", x: 64, y: 38, width: 140, height: 18, fontSize: 12, fill: "rgba(255,255,255,0.7)", fontFamily: "$--font-secondary"})

conv2=Insert(convList, {type: "rectangle", name: "会话项2", width: 228, height: 72, fill: "rgba(255,255,255,0.1)", cornerRadius: 12})
conv2Icon=Insert(conv2, {type: "ellipse", name: "会话图标", x: 12, y: 16, width: 40, height: 40, fill: "rgba(255,255,255,0.2)"})
conv2Title=Insert(conv2, {type: "text", content: "天气查询助手", x: 64, y: 16, width: 140, height: 20, fontSize: 14, fontWeight: 500, fill: "#ffffff", fontFamily: "$--font-primary"})

userSection=Insert(sidebar, {type: "frame", name: "用户信息", layout: "horizontal", width: 228, height: 60, x: 16, y: 820, gap: 12, alignItems: "center", padding: [8, 12], fill: "rgba(255,255,255,0.15)", cornerRadius: 12})
userAvatar=Insert(userSection, {type: "ellipse", name: "用户头像", width: 40, height: 40, fill: "rgba(255,255,255,0.3)"})
userName=Insert(userSection, {type: "text", content: "用户名", fontSize: 14, fontWeight: 500, fill: "#ffffff", fontFamily: "$--font-primary"})

mainArea=Insert(screen, {type: "frame", name: "主聊天区域", layout: "vertical", width: 1180, height: 900, fill: "#ffffff"})

messagesArea=Insert(mainArea, {type: "frame", name: "消息区域", layout: "vertical", width: 1180, height: 750, fill: {type: "gradient", from: "#f8fafc", to: "#edf2f7"}, padding: 32})

aiMsgBubble=Insert(messagesArea, {type: "frame", name: "AI消息气泡", layout: "horizontal", width: 680, height: 120, gap: 16, alignItems: "flex-start", padding: 20, fill: "#ffffff", cornerRadius: 20, shadow: {color: "rgba(102, 126, 234, 0.12)", blur: 20, offsetY: 4}})
aiAvatar=Insert(aiMsgBubble, {type: "ellipse", name: "AI头像", width: 44, height: 44, fill: "#667eea"})
aiContent=Insert(aiMsgBubble, {type: "text", content: "你好！有什么我可以帮助你的吗？我可以帮你编写代码、查询信息、分析数据等。", fontSize: 15, fill: "#1a202c", fontFamily: "$--font-primary", lineHeight: 1.6})

userMsgBubble=Insert(messagesArea, {type: "frame", name: "用户消息气泡", layout: "vertical", width: 680, height: 100, alignItems: "flex-end", x: 380, y: 160, padding: 20, fill: {type: "gradient", from: "#667eea", to: "#764ba2"}, cornerRadius: 20, shadow: {color: "rgba(102, 126, 234, 0.25)", blur: 20, offsetY: 4}})
userContent=Insert(userMsgBubble, {type: "text", content: "帮我写一个Python快速排序算法，要求代码简洁高效", fontSize: 15, fill: "#ffffff", fontFamily: "$--font-primary", lineHeight: 1.6, textAlign: "right"})

loadingBubble=Insert(messagesArea, {type: "frame", name: "加载动画", layout: "horizontal", width: 200, height: 60, gap: 16, alignItems: "center", x: 60, y: 300, padding: 20, fill: "#ffffff", cornerRadius: 20, shadow: {color: "rgba(102, 126, 234, 0.12)", blur: 20, offsetY: 4}})
dot1=Insert(loadingBubble, {type: "ellipse", name: "点1", width: 16, height: 16, fill: "#667eea"})
dot2=Insert(loadingBubble, {type: "ellipse", name: "点2", width: 16, height: 16, fill: "#764ba2"})
dot3=Insert(loadingBubble, {type: "ellipse", name: "点3", width: 16, height: 16, fill: "#f093fb"})

inputArea=Insert(mainArea, {type: "frame", name: "输入区域", layout: "horizontal", width: 1100, height: 80, x: 40, y: 780, gap: 12, alignItems: "center", padding: 16, fill: "rgba(255,255,255,0.95)", cornerRadius: 24, shadow: {color: "rgba(102, 126, 234, 0.15)", blur: 30, offsetY: -4}})

inputField=Insert(inputArea, {type: "rectangle", name: "输入框", width: 800, height: 48, fill: "#f7fafc", stroke: "#e2e8f0", strokeWidth: 2, cornerRadius: 24})
inputPlaceholder=Insert(inputField, {type: "text", content: "请输入消息...", fontSize: 14, fill: "#a0aec0", fontFamily: "$--font-secondary"})

deepThinkBtn=Insert(inputArea, {type: "rectangle", name: "深度思考按钮", width: 100, height: 48, fill: "transparent", stroke: {type: "gradient", from: "#667eea", to: "#764ba2"}, strokeWidth: 2, cornerRadius: 24})
deepThinkText=Insert(deepThinkBtn, {type: "text", content: "深度思考", fontSize: 13, fill: "#667eea", fontFamily: "$--font-primary"})

webSearchBtn=Insert(inputArea, {type: "rectangle", name: "联网查询按钮", width: 100, height: 48, fill: "transparent", stroke: {type: "gradient", from: "#667eea", to: "#764ba2"}, strokeWidth: 2, cornerRadius: 24})
webSearchText=Insert(webSearchBtn, {type: "text", content: "联网查询", fontSize: 13, fill: "#667eea", fontFamily: "$--font-primary"})

sendBtn=Insert(inputArea, {type: "rectangle", name: "发送按钮", width: 80, height: 48, fill: {type: "gradient", from: "#667eea", to: "#764ba2"}, cornerRadius: 24})
sendText=Insert(sendBtn, {type: "text", content: "发送", fontSize: 14, fontWeight: 600, fill: "#ffffff", fontFamily: "$--font-primary"})
