import { useEffect, useRef } from 'react'
import './StarBackground.css'

/**
 * 深空星场背景组件
 * 1:1 复刻参考代码，包括流星雨特效
 */
const StarBackground = ({ fast = false }) => {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    let animationFrameId
    let stars = []

    const resize = () => {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
      initStars()
    }

    const initStars = () => {
      stars = []
      const count = Math.floor((canvas.width * canvas.height) / 3000)
      for (let i = 0; i < count; i++) {
        stars.push({
          x: Math.random() * canvas.width,
          y: Math.random() * canvas.height,
          size: Math.random() * 1.2,
          speed: Math.random() * 0.15 + 0.05,
          opacity: Math.random() * 0.7
        })
      }
    }

    const draw = () => {
      // 1:1 复刻参考代码：fast 模式下也是纯黑背景，无拖尾效果
      ctx.fillStyle = '#000'
      ctx.fillRect(0, 0, canvas.width, canvas.height)

      const speedMultiplier = fast ? 40 : 1

      stars.forEach(star => {
        ctx.fillStyle = `rgba(255, 255, 255, ${star.opacity})`
        ctx.beginPath()
        if (fast) {
          // 1:1 复刻参考代码：垂直方向的矩形线条
          ctx.rect(star.x, star.y, 1, star.speed * speedMultiplier * 10)
        } else {
          // 正常模式：绘制圆点
          ctx.arc(star.x, star.y, star.size, 0, Math.PI * 2)
        }
        ctx.fill()

        // 1:1 复刻参考代码：垂直向上移动
        star.y -= star.speed * speedMultiplier
        if (star.y < 0) {
          star.y = canvas.height
          star.x = Math.random() * canvas.width
        }
      })

      animationFrameId = requestAnimationFrame(draw)
    }

    window.addEventListener('resize', resize)
    resize()
    draw()

    return () => {
      window.removeEventListener('resize', resize)
      cancelAnimationFrame(animationFrameId)
    }
  }, [fast])

  return <canvas ref={canvasRef} className="starfield-canvas" />
}

export default StarBackground
