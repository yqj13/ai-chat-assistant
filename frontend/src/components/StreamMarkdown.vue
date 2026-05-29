<template>
  <div class="stream-markdown" ref="containerRef">
    <div ref="markdownRef" class="markdown-body"></div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { marked } from 'marked'
import hljs from 'highlight.js'
import katex from 'katex'
import mermaid from 'mermaid'
import TypeIt from 'typeit'

const props = defineProps({
  content: {
    type: String,
    default: ''
  },
  // 是否启用打字机效果
  typing: {
    type: Boolean,
    default: false
  },
  // 打字速度（ms / 步骤）
  speed: {
    type: Number,
    default: 20
  },
  // 光标设置
  cursor: {
    type: [Boolean, Object],
    default: true
  },
  // 是否在完成后移除光标
  cursorRemoveOnComplete: {
    type: Boolean,
    default: true
  },
  // 是否启用 LaTeX
  enableLatex: {
    type: Boolean,
    default: true
  },
  // 是否启用 Mermaid
  enableMermaid: {
    type: Boolean,
    default: true
  },
  // 是否打字完成后再渲染 Mermaid（避免中间态）
  deferMermaid: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['start', 'complete', 'step'])

const containerRef = ref(null)
const markdownRef = ref(null)

let typeItInstance = null
let previousContent = ''
let isDestroyed = false
let renderTimer = null

// ========================
// Marked 配置
// ========================

const escapeHtml = (text) => {
  const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }
  return text.replace(/[&<>"']/g, m => map[m])
}

const configureMarked = () => {
  const renderer = new marked.Renderer()

  renderer.code = (code, language) => {
    // Mermaid 代码块特殊处理
    if (language === 'mermaid') {
      return `<div class="mermaid-placeholder" data-mermaid="${escapeHtml(code)}"><pre><code class="language-mermaid">${escapeHtml(code)}</code></pre></div>`
    }

    const validLang = hljs.getLanguage(language) ? language : 'plaintext'
    const highlighted = hljs.highlight(code, { language: validLang }).value

    return `<div class="code-block-wrapper">
      <div class="code-block-header">
        <span class="code-language">${validLang}</span>
        <button class="copy-btn" data-code="${escapeHtml(code)}">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
          </svg>
          <span>复制</span>
        </button>
      </div>
      <pre><code class="hljs language-${validLang}">${highlighted}</code></pre>
    </div>`
  }

  renderer.codespan = (code) => {
    return `<code class="inline-code">${escapeHtml(code)}</code>`
  }

  renderer.link = (href, title, text) => {
    const t = title ? ` title="${title}"` : ''
    return `<a href="${href}"${t} target="_blank" rel="noopener noreferrer">${text}</a>`
  }

  renderer.table = (header, body) => {
    return `<div class="table-wrapper"><table><thead>${header}</thead><tbody>${body}</tbody></table></div>`
  }

  marked.setOptions({
    renderer,
    breaks: true,
    gfm: true
  })
}

// ========================
// LaTeX 处理
// ========================

const processLatex = (text) => {
  if (!props.enableLatex) return text

  // 块级公式 \[...\]（MathJax 格式）
  text = text.replace(/\\\[([\s\S]+?)\\\]/g, (_, formula) => {
    try {
      return `<div class="latex-block">${katex.renderToString(formula.trim(), { displayMode: true, throwOnError: false })}</div>`
    } catch (e) {
      return `<div class="latex-error">\\[${formula}\\]</div>`
    }
  })

  // 行内公式 \(...\)（MathJax 格式）- 修复：支持包含 LaTeX 命令的内容
  text = text.replace(/\\\(([\s\S]+?)\\\)/g, (_, formula) => {
    try {
      return `<span class="latex-inline">${katex.renderToString(formula.trim(), { displayMode: false, throwOnError: false })}</span>`
    } catch (e) {
      return `<span class="latex-error">\\(${formula}\\)</span>`
    }
  })

  // 块级公式 $$...$$（KaTeX 标准格式）
  text = text.replace(/\$\$([\s\S]+?)\$\$/g, (_, formula) => {
    try {
      return `<div class="latex-block">${katex.renderToString(formula.trim(), { displayMode: true, throwOnError: false })}</div>`
    } catch (e) {
      return `<div class="latex-error">$$${formula}$$</div>`
    }
  })

  // 行内公式 $...$（排除 $$ 和代码中的 $）
  text = text.replace(/(?<!\$)\$(?!\$)([^\$\n]+?)\$(?!\$)/g, (_, formula) => {
    try {
      return `<span class="latex-inline">${katex.renderToString(formula.trim(), { displayMode: false, throwOnError: false })}</span>`
    } catch (e) {
      return `<span class="latex-error">$${formula}$</span>`
    }
  })

  return text
}

// ========================
// Mermaid 处理
// ========================

const renderMermaidBlocks = async () => {
  if (!props.enableMermaid || !markdownRef.value) return

  const placeholders = markdownRef.value.querySelectorAll('.mermaid-placeholder')
  
  for (let i = 0; i < placeholders.length; i++) {
    const el = placeholders[i]
    const code = el.getAttribute('data-mermaid')
    if (!code) continue

    const id = `mermaid-${Date.now()}-${i}-${Math.random().toString(36).substring(2, 8)}`
    try {
      const { svg } = await mermaid.render(id, code)
      el.innerHTML = `<div class="mermaid-rendered">${svg}</div>`
      el.classList.remove('mermaid-placeholder')
      el.classList.add('mermaid-wrapper')
    } catch (e) {
      el.innerHTML = `<div class="mermaid-error">Mermaid 渲染失败: ${e.message}</div>`
    }
  }
}

// ========================
// Markdown 渲染
// ========================

const renderMarkdown = (text) => {
  if (!text) return ''
  const withLatex = processLatex(text)
  return marked.parse(withLatex)
}

// ========================
// TypeIt 打字机实例管理
// ========================

const destroyTypeIt = () => {
  if (typeItInstance) {
    try {
      typeItInstance.destroy()
    } catch (e) {
      // TypeIt 可能已销毁
    }
    typeItInstance = null
  }
}

/**
 * 核心：流式打字机渲染
 * 
 * 策略：
 * - 将已渲染的 HTML 作为整体输入 TypeIt
 * - TypeIt 使用 html: true 配置逐步呈现 HTML
 * - 每次 content 变化时，计算增量并追加到 TypeIt 队列
 */
const startTypeIt = (html) => {
  if (!markdownRef.value || isDestroyed) return

  destroyTypeIt()

  // 清空容器
  markdownRef.value.innerHTML = ''

  const cursorConfig = props.cursor === false
    ? false
    : props.cursor === true
      ? { speed: 1000, autoPause: true }
      : props.cursor

  typeItInstance = new TypeIt(markdownRef.value, {
    speed: props.speed,
    html: true,
    cursor: cursorConfig,
    waitUntilVisible: false,
    afterComplete: async (instance) => {
      // 打字完成后处理
      if (props.cursorRemoveOnComplete) {
        instance.destroy()
      }
      // 渲染 Mermaid
      await renderMermaidBlocks()
      emit('complete')
    },
    afterStep: () => {
      emit('step')
      // 自动滚动
      scrollToBottom()
    }
  })
    .type(html, { instant: false })
    .go()

  emit('start')
}

/**
 * 增量更新策略：
 * 对于流式数据，我们不能每次重建 TypeIt，
 * 而是采用"分段渲染"的方式：
 * - 已完成的部分：直接展示（instant）
 * - 新增的部分：打字机效果展示
 */
const updateContent = async (newContent) => {
  if (!markdownRef.value || isDestroyed) return

  const newHtml = renderMarkdown(newContent)

  if (!props.typing) {
    // 不使用打字机效果，直接渲染
    markdownRef.value.innerHTML = newHtml
    await nextTick()
    await renderMermaidBlocks()
    bindCopyButtons()
    return
  }

  // 流式场景：内容持续增长
  if (newContent === previousContent) return

  // 计算已展示和新增部分
  const oldHtml = previousContent ? renderMarkdown(previousContent) : ''
  const incrementalHtml = newHtml

  previousContent = newContent

  // 如果 TypeIt 未初始化或者内容完全变化
  if (!typeItInstance || !newContent.startsWith(previousContent.slice(0, -50))) {
    destroyTypeIt()
    markdownRef.value.innerHTML = ''

    const cursorConfig = props.cursor === false
      ? false
      : { speed: 800 }

    typeItInstance = new TypeIt(markdownRef.value, {
      speed: props.speed,
      html: true,
      cursor: cursorConfig,
      waitUntilVisible: false,
      afterComplete: async () => {
        await renderMermaidBlocks()
        bindCopyButtons()
        emit('complete')
      },
      afterStep: () => {
        emit('step')
        scrollToBottom()
      }
    })
      .type(incrementalHtml)
      .go()

    emit('start')
  }
}

/**
 * 简化方案：使用防抖 + 分块渲染
 * 
 * 由于 TypeIt 对动态追加的支持有限，
 * 采用更可靠的"逐块打字"方案
 */
const streamBuffer = ref('')
const isTypingActive = ref(false)
let charQueue = []
let typingRAF = null

const startStreamTyping = () => {
  if (isTypingActive.value) return
  isTypingActive.value = true
  processQueue()
}

const processQueue = () => {
  if (isDestroyed || !markdownRef.value) {
    isTypingActive.value = false
    return
  }

  if (charQueue.length === 0) {
    isTypingActive.value = false
    // 队列清空后做最终渲染
    finalRender()
    return
  }

  // 每帧处理多个字符（根据 speed 计算）
  const charsPerFrame = Math.max(1, Math.ceil(16 / props.speed))
  const chunk = charQueue.splice(0, charsPerFrame).join('')
  streamBuffer.value += chunk

  // 渲染当前缓冲的内容
  const html = renderMarkdown(streamBuffer.value)
  markdownRef.value.innerHTML = html
  
  scrollToBottom()
  emit('step')

  typingRAF = requestAnimationFrame(() => {
    setTimeout(processQueue, props.speed)
  })
}

const finalRender = async () => {
  if (!markdownRef.value) return
  const html = renderMarkdown(streamBuffer.value)
  markdownRef.value.innerHTML = html
  await nextTick()
  await renderMermaidBlocks()
  bindCopyButtons()
}

const stopStreamTyping = () => {
  if (typingRAF) {
    cancelAnimationFrame(typingRAF)
    typingRAF = null
  }
  isTypingActive.value = false
  charQueue = []
}

// ========================
// TypeIt 完整方案（非流式，内容完整时使用）
// ========================

const typeFullContent = (content) => {
  if (!markdownRef.value || isDestroyed) return

  destroyTypeIt()
  markdownRef.value.innerHTML = ''

  const html = renderMarkdown(content)

  const cursorOpts = props.cursor === false
    ? false
    : typeof props.cursor === 'object'
      ? props.cursor
      : { speed: 800 }

  typeItInstance = new TypeIt(markdownRef.value, {
    speed: props.speed,
    html: true,
    cursor: cursorOpts,
    waitUntilVisible: false,
    afterComplete: async (instance) => {
      if (props.cursorRemoveOnComplete) {
        // 移除光标
        const cursorEl = markdownRef.value?.querySelector('.ti-cursor')
        if (cursorEl) cursorEl.remove()
      }
      await renderMermaidBlocks()
      bindCopyButtons()
      emit('complete')
    },
    afterStep: () => {
      emit('step')
      scrollToBottom()
    }
  })
    .type(html)
    .go()

  emit('start')
}

// ========================
// 监听 content 变化（流式模式核心）
// ========================

watch(
  () => props.content,
  (newVal, oldVal) => {
    if (isDestroyed) return

    if (!props.typing) {
      // 非打字机模式：直接渲染
      directRender(newVal)
      return
    }

    if (!newVal) {
      streamBuffer.value = ''
      charQueue = []
      if (markdownRef.value) markdownRef.value.innerHTML = ''
      return
    }

    // 流式场景：内容增长
    if (newVal.startsWith(oldVal || '')) {
      const increment = newVal.slice((oldVal || '').length)
      if (increment) {
        charQueue.push(...increment.split(''))
        startStreamTyping()
      }
    } else {
      // 内容完全改变，重置
      stopStreamTyping()
      streamBuffer.value = ''
      charQueue = newVal.split('')
      startStreamTyping()
    }
  },
  { immediate: true }
)

// 当 typing 变为 false 时，立即展示全部内容
watch(
  () => props.typing,
  (newVal) => {
    if (!newVal && props.content) {
      stopStreamTyping()
      destroyTypeIt()
      streamBuffer.value = props.content
      directRender(props.content)
      emit('complete')
    }
  }
)

// ========================
// 直接渲染（无动画）
// ========================

const directRender = async (content) => {
  if (!markdownRef.value) return
  const html = renderMarkdown(content || '')
  markdownRef.value.innerHTML = html
  await nextTick()
  await renderMermaidBlocks()
  bindCopyButtons()
}

// ========================
// 辅助方法
// ========================

const scrollToBottom = () => {
  if (!containerRef.value) return
  const scrollParent = findScrollParent(containerRef.value)
  if (scrollParent) {
    scrollParent.scrollTo({
      top: scrollParent.scrollHeight,
      behavior: 'smooth'
    })
  }
}

const findScrollParent = (el) => {
  let parent = el.parentElement
  while (parent) {
    const { overflow, overflowY } = window.getComputedStyle(parent)
    if (/(auto|scroll)/.test(overflow + overflowY)) {
      return parent
    }
    parent = parent.parentElement
  }
  return null
}

const bindCopyButtons = () => {
  if (!markdownRef.value) return
  const buttons = markdownRef.value.querySelectorAll('.copy-btn')
  buttons.forEach(btn => {
    // 防止重复绑定
    if (btn.dataset.bound) return
    btn.dataset.bound = 'true'

    btn.addEventListener('click', async () => {
      const code = btn.getAttribute('data-code')
      if (!code) return
      try {
        await navigator.clipboard.writeText(code)
        const span = btn.querySelector('span')
        if (span) {
          const orig = span.textContent
          span.textContent = '已复制!'
          btn.classList.add('copied')
          setTimeout(() => {
            span.textContent = orig
            btn.classList.remove('copied')
          }, 2000)
        }
      } catch (e) {
        console.error('复制失败:', e)
      }
    })
  })
}

// ========================
// 生命周期
// ========================

onMounted(() => {
  configureMarked()

  if (props.enableMermaid) {
    mermaid.initialize({
      startOnLoad: false,
      theme: 'default',
      securityLevel: 'loose',
      fontFamily: 'inherit'
    })
  }

  // 初始内容
  if (props.content) {
    if (props.typing) {
      charQueue = props.content.split('')
      startStreamTyping()
    } else {
      directRender(props.content)
    }
  }
})

onUnmounted(() => {
  isDestroyed = true
  stopStreamTyping()
  destroyTypeIt()
  if (renderTimer) {
    clearTimeout(renderTimer)
    renderTimer = null
  }
})

// 暴露方法
defineExpose({
  /** 手动停止打字并立即显示全部内容 */
  flush: () => {
    stopStreamTyping()
    destroyTypeIt()
    streamBuffer.value = props.content
    directRender(props.content)
  },
  /** 重新开始打字 */
  restart: () => {
    stopStreamTyping()
    destroyTypeIt()
    streamBuffer.value = ''
    charQueue = props.content.split('')
    startStreamTyping()
  }
})
</script>

<style scoped>
.stream-markdown {
  position: relative;
  line-height: 1.7;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

/* TypeIt 光标样式 */
.stream-markdown :deep(.ti-cursor) {
  font-weight: 100;
  color: #333;
  font-size: 1.1em;
  opacity: 1;
  animation: ti-blink 0.7s infinite;
}

@keyframes ti-blink {
  0% { opacity: 1; }
  50% { opacity: 0; }
}

/* ========================================
   Markdown 基础排版
   ======================================== */

.markdown-body {
  font-size: 15px;
  color: #1f2328;
  line-height: 1.75;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4),
.markdown-body :deep(h5),
.markdown-body :deep(h6) {
  margin-top: 24px;
  margin-bottom: 16px;
  font-weight: 600;
  line-height: 1.3;
}

.markdown-body :deep(h1) { font-size: 1.8em; border-bottom: 1px solid #d1d9e0; padding-bottom: 0.3em; }
.markdown-body :deep(h2) { font-size: 1.5em; border-bottom: 1px solid #d1d9e0; padding-bottom: 0.3em; }
.markdown-body :deep(h3) { font-size: 1.25em; }
.markdown-body :deep(h4) { font-size: 1em; }
.markdown-body :deep(h5) { font-size: 0.875em; }
.markdown-body :deep(h6) { font-size: 0.85em; color: #656d76; }

.markdown-body :deep(p) {
  margin: 0 0 16px;
}

.markdown-body :deep(strong) {
  font-weight: 600;
}

.markdown-body :deep(a) {
  color: #0969da;
  text-decoration: none;
}

.markdown-body :deep(a:hover) {
  text-decoration: underline;
}

/* 列表 */
.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  padding-left: 2em;
  margin: 0 0 16px;
}

.markdown-body :deep(li) {
  margin-bottom: 4px;
}

.markdown-body :deep(li + li) {
  margin-top: 4px;
}

/* 引用 */
.markdown-body :deep(blockquote) {
  margin: 16px 0;
  padding: 4px 16px;
  color: #636c76;
  border-left: 4px solid #d0d7de;
  background: #f6f8fa;
  border-radius: 0 6px 6px 0;
}

.markdown-body :deep(blockquote > :first-child) { margin-top: 0; }
.markdown-body :deep(blockquote > :last-child) { margin-bottom: 0; }

/* 分隔线 */
.markdown-body :deep(hr) {
  height: 3px;
  padding: 0;
  margin: 24px 0;
  background-color: #d0d7de;
  border: 0;
  border-radius: 2px;
}

/* 行内代码 */
.markdown-body :deep(.inline-code) {
  padding: 0.2em 0.4em;
  margin: 0 2px;
  font-size: 85%;
  background-color: #eff1f3;
  border-radius: 6px;
  font-family: 'JetBrains Mono', 'Fira Code', 'SF Mono', monospace;
  color: #1f2328;
}

/* ========================================
   代码块
   ======================================== */

.markdown-body :deep(.code-block-wrapper) {
  margin: 16px 0;
  border-radius: 10px;
  overflow: hidden;
  background: #1e1e2e;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.markdown-body :deep(.code-block-header) {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  background: #181825;
  border-bottom: 1px solid #313244;
}

.markdown-body :deep(.code-language) {
  font-size: 12px;
  color: #a6adc8;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-family: 'JetBrains Mono', monospace;
}

.markdown-body :deep(.copy-btn) {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  font-size: 12px;
  color: #a6adc8;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid #45475a;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: inherit;
}

.markdown-body :deep(.copy-btn:hover) {
  background: rgba(255, 255, 255, 0.1);
  border-color: #89b4fa;
  color: #89b4fa;
}

.markdown-body :deep(.copy-btn.copied) {
  color: #a6e3a1;
  border-color: #a6e3a1;
}

.markdown-body :deep(.code-block-wrapper pre) {
  margin: 0;
  padding: 16px;
  overflow-x: auto;
  background: #1e1e2e;
}

.markdown-body :deep(.code-block-wrapper pre::-webkit-scrollbar) {
  height: 6px;
}

.markdown-body :deep(.code-block-wrapper pre::-webkit-scrollbar-thumb) {
  background: #45475a;
  border-radius: 3px;
}

.markdown-body :deep(.code-block-wrapper code) {
  font-family: 'JetBrains Mono', 'Fira Code', 'SF Mono', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: #cdd6f4;
  background: transparent;
}

/* ========================================
   表格
   ======================================== */

.markdown-body :deep(.table-wrapper) {
  overflow-x: auto;
  margin: 16px 0;
  border-radius: 8px;
  border: 1px solid #d0d7de;
}

.markdown-body :deep(table) {
  border-collapse: collapse;
  width: 100%;
}

.markdown-body :deep(th),
.markdown-body :deep(td) {
  padding: 10px 16px;
  border: 1px solid #d0d7de;
  text-align: left;
}

.markdown-body :deep(th) {
  background-color: #f6f8fa;
  font-weight: 600;
}

.markdown-body :deep(tr:nth-child(even)) {
  background-color: #f6f8fa;
}

/* ========================================
   LaTeX
   ======================================== */

.markdown-body :deep(.latex-block) {
  margin: 20px 0;
  padding: 20px;
  overflow-x: auto;
  background: #f6f8fa;
  border-radius: 8px;
  text-align: center;
  border: 1px solid #e8ecf0;
}

.markdown-body :deep(.latex-inline) {
  display: inline-block;
  margin: 0 3px;
  vertical-align: middle;
}

.markdown-body :deep(.latex-error) {
  color: #cf222e;
  background: #ffebe9;
  padding: 4px 8px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 13px;
}

/* ========================================
   Mermaid
   ======================================== */

.markdown-body :deep(.mermaid-wrapper) {
  margin: 20px 0;
  padding: 24px;
  background: #f6f8fa;
  border-radius: 10px;
  text-align: center;
  overflow-x: auto;
  border: 1px solid #e8ecf0;
}

.markdown-body :deep(.mermaid-rendered svg) {
  max-width: 100%;
  height: auto;
}

.markdown-body :deep(.mermaid-placeholder) {
  margin: 16px 0;
  padding: 16px;
  background: #f6f8fa;
  border-radius: 8px;
  border: 1px dashed #d0d7de;
}

.markdown-body :deep(.mermaid-error) {
  margin: 16px 0;
  padding: 16px;
  background: #ffebe9;
  border: 1px solid #ff8182;
  border-radius: 8px;
  color: #cf222e;
  font-family: monospace;
  font-size: 13px;
}

/* ========================================
   图片
   ======================================== */

.markdown-body :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
  margin: 16px 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* ========================================
   任务列表
   ======================================== */

.markdown-body :deep(input[type="checkbox"]) {
  margin-right: 6px;
  transform: scale(1.1);
}
</style>