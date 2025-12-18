import { useState, useEffect, useRef } from 'react'
import { getMomentsAPI } from '../services/api'
import MomentCard from './MomentCard'
import StarBackground from './StarBackground'
import './MemoriesView.css'

function MemoriesView({ userInfo, onClose }) {
  const [moments, setMoments] = useState([])
  const [loading, setLoading] = useState(false)
  const [selectedMoment, setSelectedMoment] = useState(null)
  
  // --- 新增：相机状态 ---
  const [camera, setCamera] = useState({ 
    rotY: 0,      // Y轴旋转
    rotX: 0,      // X轴旋转（可选）
    zoom: 1,      // 缩放
    offsetX: 0,   // X轴平移
    offsetY: 0    // Y轴平移
  })
  const isDragging = useRef(false)
  const lastMouse = useRef({ x: 0, y: 0 })

  const loadMoments = async () => {
    try {
      setLoading(true)
      const result = await getMomentsAPI(userInfo.user_id)
      setMoments(result.moments || [])
    } catch (error) {
      console.error('加载 Moments 失败:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadMoments()
  }, [userInfo.user_id])

  // 获取情绪颜色
  const getEmotionColor = (emotion) => {
    const emotionMap = {
      'joy': '#FFD700',
      'sadness': '#9370DB',
      'anger': '#FF6347',
      'fear': '#4682B4',
      'love': '#FF69B4',
      'surprise': '#FFA500',
      'neutral': '#D3D3D3',
    }
    return emotionMap[emotion?.toLowerCase()] || emotionMap['neutral']
  }

  // 3D 星图渲染逻辑（基于时间的坐标系统）
  const timeRef = useRef(0)
  
  useEffect(() => {
    if (moments.length === 0) {
      const canvas = document.getElementById('nebula-canvas')
      if (canvas) {
        const ctx = canvas.getContext('2d')
        ctx.clearRect(0, 0, canvas.width, canvas.height)
      }
      return
    }

    const canvas = document.getElementById('nebula-canvas')
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    let animationFrameId

    // 自适应容器大小
    const resizeCanvas = () => {
      const container = canvas.parentElement
      if (container) {
        const rect = container.getBoundingClientRect()
        canvas.width = rect.width
        canvas.height = rect.height
      }
    }
    
    resizeCanvas()
    
    // 监听窗口大小变化
    const handleResize = () => {
      resizeCanvas()
    }
    window.addEventListener('resize', handleResize)

    // --- 核心：3D 坐标转换函数 ---
    const get3DPosition = (index, total, time, camera) => {
      // 1. 时间轴分布：最新的在前面（index=0 最前面）
      const spacing = 40 // 星体之间的间距
      const zBase = index * spacing - (time * 10) // 基础 Z 轴，随时间缓慢漂移
      
      // 2. 螺旋状布局，形成星轨图
      const angle = index * 0.4 + (camera.rotY * 0.5)
      const radius = 150 * (1 + index * 0.05) // 越往后半径越大，形成漏斗状或螺旋状
      
      // 初始 3D 坐标
      let x = Math.cos(angle) * radius
      let y = Math.sin(angle) * radius + (index * 10) // 纵向稍微错开
      let z = zBase

      // 3. 应用相机旋转 (绕 Y 轴)
      const cosRY = Math.cos(camera.rotY)
      const sinRY = Math.sin(camera.rotY)
      const rx = x * cosRY - z * sinRY
      const rz = x * sinRY + z * cosRY

      // 4. 透视投影
      const perspective = 600 * camera.zoom
      const scale = perspective / (perspective + rz + 500) // 500 是初始深度偏移
      
      return {
        x: canvas.width / 2 + rx * scale + camera.offsetX,
        y: canvas.height / 2 + y * scale + camera.offsetY,
        scale: scale,
        opacity: Math.max(0, Math.min(1, scale * 1.5)), // 越远越透明
        zIndex: rz
      }
    }

    const animate = () => {
      timeRef.current += 0.002 // 极慢的移动
      const t = timeRef.current
      
      const width = canvas.width
      const height = canvas.height
      
      ctx.clearRect(0, 0, width, height)

      // 按时间排序：最新的在前面（timestamp 大的在前）
      const sortedMoments = [...moments].sort((a, b) => {
        const timeA = a.timestamp ? new Date(a.timestamp).getTime() : 0
        const timeB = b.timestamp ? new Date(b.timestamp).getTime() : 0
        return timeB - timeA // 降序：最新的在前
      })

      // 预计算所有点的 3D 位置
      const points = sortedMoments.map((m, i) => ({
        ...m,
        ...get3DPosition(i, sortedMoments.length, t, camera)
      }))

      // 1. 绘制连线 (增强星图感)
      ctx.beginPath()
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)'
      ctx.lineWidth = 1
      for (let i = 0; i < points.length - 1; i++) {
        if (points[i].scale > 0 && points[i+1].scale > 0) {
          ctx.moveTo(points[i].x, points[i].y)
          ctx.lineTo(points[i+1].x, points[i+1].y)
        }
      }
      ctx.stroke()

      // 2. 绘制星体 (深度排序：先画远的)
      points.sort((a, b) => b.zIndex - a.zIndex).forEach((p) => {
        const color = p.color || getEmotionColor(p.emotion_tag) || '#D3D3D3'
        const size = 25 * p.scale // 基础大小随远近变化

        // 呼吸感而非闪烁（极慢的脉冲）
        const pulse = Math.sin(t * 2 + p.zIndex) * 0.1 + 0.9
        const finalSize = size * pulse

        // 电影级质感：减少光晕亮度，增加核心凝聚力
        const grad = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, finalSize * 2)
        grad.addColorStop(0, '#FFFFFF')
        grad.addColorStop(0.2, color)
        grad.addColorStop(0.6, color + '33') // 调低透明度，增加深邃感
        grad.addColorStop(1, 'transparent')

        ctx.globalAlpha = p.opacity
        ctx.fillStyle = grad
        ctx.beginPath()
        ctx.arc(p.x, p.y, finalSize * 2.5, 0, Math.PI * 2)
        ctx.fill()
        
        // 绘制小核心增强实体感
        ctx.beginPath()
        ctx.fillStyle = '#FFFFFF'
        ctx.globalAlpha = p.opacity * 0.5
        ctx.arc(p.x, p.y, finalSize * 0.3, 0, Math.PI * 2)
        ctx.fill()
        
        ctx.globalAlpha = 1
      })

      animationFrameId = requestAnimationFrame(animate)
    }

    animate()

    // 添加点击事件（更新后的点击判定逻辑）
    const handleCanvasClick = (e) => {
      const rect = canvas.getBoundingClientRect()
      const mouseX = e.clientX - rect.left
      const mouseY = e.clientY - rect.top
      
      // 计算缩放比例
      const scaleX = canvas.width / rect.width
      const scaleY = canvas.height / rect.height
      const clickX = mouseX * scaleX
      const clickY = mouseY * scaleY
      
      // 获取当前时刻的渲染位置
      const t = timeRef.current
      const sortedMoments = [...moments].sort((a, b) => {
        const timeA = a.timestamp ? new Date(a.timestamp).getTime() : 0
        const timeB = b.timestamp ? new Date(b.timestamp).getTime() : 0
        return timeB - timeA
      })
      
      const points = sortedMoments.map((m, i) => ({
        ...m,
        ...get3DPosition(i, sortedMoments.length, t, camera)
      }))
      
      // 找到距离点击位置最近的星体
      let closestMoment = null
      let minDistance = Infinity
      
      points.forEach((p) => {
        const size = 25 * p.scale
        const pulse = Math.sin(t * 2 + p.zIndex) * 0.1 + 0.9
        const finalSize = size * pulse
        const clickRadius = finalSize * 2.5 // 点击范围等于光晕半径
        
        const distance = Math.sqrt(
          Math.pow(clickX - p.x, 2) + 
          Math.pow(clickY - p.y, 2)
        )
        
        if (distance < clickRadius && distance < minDistance) {
          minDistance = distance
          closestMoment = p
        }
      })
      
      if (closestMoment) {
        handleStarClick(closestMoment)
      }
    }

    canvas.addEventListener('click', handleCanvasClick)
    
    return () => {
      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId)
      }
      canvas.removeEventListener('click', handleCanvasClick)
      window.removeEventListener('resize', handleResize)
    }
  }, [moments, camera])

  const handleStarClick = (moment) => {
    setSelectedMoment({
      moment_id: moment.moment_id,
      title: moment.title,
      summary: moment.summary,
      emotion: moment.emotion_tag,
      timestamp: moment.timestamp,
      color: moment.color
    })
  }

  // --- 新增：交互逻辑 ---
  const handleMouseDown = (e) => {
    // 只在canvas区域拖拽
    if (e.target.id === 'nebula-canvas') {
      isDragging.current = true
      lastMouse.current = { x: e.clientX, y: e.clientY }
    }
  }

  const handleMouseMove = (e) => {
    if (!isDragging.current) return
    const deltaX = e.clientX - lastMouse.current.x
    const deltaY = e.clientY - lastMouse.current.y
    
    setCamera(prev => ({
      ...prev,
      rotY: prev.rotY + deltaX * 0.01,
      offsetX: prev.offsetX + deltaX * 0.5, // 同步支持平移
      offsetY: prev.offsetY + deltaY * 0.5
    }))
    
    lastMouse.current = { x: e.clientX, y: e.clientY }
  }

  const handleMouseUp = () => { 
    isDragging.current = false 
  }

  const handleWheel = (e) => {
    // 只在canvas区域缩放
    if (e.target.id === 'nebula-canvas') {
      e.preventDefault()
      setCamera(prev => ({
        ...prev,
        zoom: Math.max(0.5, Math.min(2, prev.zoom - e.deltaY * 0.001))
      }))
    }
  }

  if (loading) {
    return (
      <div className="memories-view">
        <div className="memory-nebula-header">
          <h1>FLIGHT LOGS</h1>
          <p className="nebula-status">Loading...</p>
        </div>
      </div>
    )
  }

  return (
    <div 
      className="memories-view"
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onWheel={handleWheel}
    >
      {/* 星场背景 */}
      <StarBackground fast={false} />
      
      {/* Memory Nebula 头部 */}
      <div className="memory-nebula-header">
        <h1>FLIGHT LOGS</h1>
        {moments.length === 0 ? (
          <p className="nebula-status">AWAITING FRAGMENTS...</p>
        ) : (
          <>
            <p className="nebula-status">{moments.length} ECHOES CAPTURED IN STREAMS</p>
            <p className="nebula-hint">SYNC TO RECOLLECT...</p>
          </>
        )}
        {/* 关闭按钮（右上角） */}
        <button 
          className="memories-close-btn"
          onClick={() => {
            if (onClose) {
              onClose()
            } else {
              window.history.back()
            }
          }}
          aria-label="Close"
        >
          ×
        </button>
      </div>

      {/* 星轨图（Canvas 渲染） */}
      <div className="nebula-canvas-container">
        <canvas 
          id="nebula-canvas" 
          className="nebula-canvas"
        />
      </div>


      {/* Moment Card 显示 */}
      {selectedMoment && (
        <MomentCard 
          card={selectedMoment} 
          onClose={() => setSelectedMoment(null)}
        />
      )}
    </div>
  )
}

export default MemoriesView
