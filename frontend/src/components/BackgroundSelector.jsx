import { useState, useRef, useEffect } from 'react'
import './BackgroundSelector.css'

const BackgroundSelector = ({ onSelect, backgroundImages }) => {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isTransitioning, setIsTransitioning] = useState(false)
  const [isSelected, setIsSelected] = useState(false)
  const containerRef = useRef(null)
  const carouselRef = useRef(null)
  const startXRef = useRef(0)
  const currentXRef = useRef(0)
  const isDraggingRef = useRef(false)
  const rotationYRef = useRef(0)

  // 触摸/鼠标事件处理
  const handleStart = (clientX) => {
    if (isSelected || isTransitioning) return
    isDraggingRef.current = true
    startXRef.current = clientX
    currentXRef.current = clientX
  }

  const handleMove = (clientX) => {
    if (!isDraggingRef.current || isSelected || isTransitioning) return
    
    const deltaX = clientX - startXRef.current
    const sensitivity = 0.5 // 滑动敏感度
    rotationYRef.current = deltaX * sensitivity
    
    // 更新carousel的旋转
    if (carouselRef.current) {
      carouselRef.current.style.transform = `perspective(1000px) rotateY(${rotationYRef.current}deg) translateZ(0)`
    }
  }

  const handleEnd = () => {
    if (!isDraggingRef.current || isSelected || isTransitioning) return
    isDraggingRef.current = false

    // 根据滑动距离决定是否切换图片
    const threshold = 50 // 滑动阈值
    if (Math.abs(rotationYRef.current) > threshold) {
      if (rotationYRef.current > 0) {
        // 向右滑动，显示前一张
        setCurrentIndex((prev) => (prev > 0 ? prev - 1 : backgroundImages.length - 1))
      } else {
        // 向左滑动，显示下一张
        setCurrentIndex((prev) => (prev < backgroundImages.length - 1 ? prev + 1 : 0))
      }
    }
    
    // 重置旋转
    rotationYRef.current = 0
    if (carouselRef.current) {
      carouselRef.current.style.transform = `perspective(1000px) rotateY(0deg) translateZ(0)`
    }
  }

  // 鼠标事件
  const handleMouseDown = (e) => {
    e.preventDefault()
    handleStart(e.clientX)
  }

  const handleMouseMove = (e) => {
    handleMove(e.clientX)
  }

  const handleMouseUp = () => {
    handleEnd()
  }

  // 触摸事件
  const handleTouchStart = (e) => {
    handleStart(e.touches[0].clientX)
  }

  const handleTouchMove = (e) => {
    handleMove(e.touches[0].clientX)
  }

  const handleTouchEnd = () => {
    handleEnd()
  }

  // 点击选中图片
  const handleImageClick = (index) => {
    if (isSelected || isTransitioning) return
    
    // 如果点击的不是当前图片，先切换到该图片
    if (index !== currentIndex) {
      setCurrentIndex(index)
      // 等待切换动画完成后再触发选中
      setTimeout(() => {
        handleSelect(index)
      }, 300)
    } else {
      handleSelect(index)
    }
  }

  // 选中图片并触发下沉动画
  const handleSelect = (index) => {
    setIsSelected(true)
    setIsTransitioning(true)
    
    // 确保选中的图片切换到中心位置
    setCurrentIndex(index)
    
    // 等待切换动画完成后再触发下沉
    setTimeout(() => {
      // 触发下沉动画
      if (containerRef.current) {
        containerRef.current.classList.add('sinking')
      }
      
      // 等待下沉动画完成后，通知父组件
      setTimeout(() => {
        if (onSelect) {
          onSelect(backgroundImages[index], index)
        }
      }, 800) // 下沉动画时长
    }, 300) // 等待切换动画完成
  }

  // 计算每张图片的3D变换
  const getImageTransform = (index) => {
    const offset = index - currentIndex
    const distance = Math.abs(offset)
    const angle = offset * 45 // 每张图片旋转45度
    
    // 计算z轴偏移（形成环绕感）
    const zOffset = -Math.abs(offset) * 200
    
    // 计算缩放（中心图片最大，两边逐渐缩小）
    const scale = 1 - distance * 0.2
    const opacity = 1 - distance * 0.3
    
    return {
      transform: `translateX(${offset * 300}px) translateZ(${zOffset}px) rotateY(${angle}deg) scale(${scale})`,
      opacity: Math.max(0.3, opacity),
      zIndex: backgroundImages.length - distance
    }
  }

  useEffect(() => {
    // 添加全局事件监听（用于鼠标拖拽）
    if (!isSelected) {
      window.addEventListener('mousemove', handleMouseMove)
      window.addEventListener('mouseup', handleMouseUp)
    }
    
    return () => {
      window.removeEventListener('mousemove', handleMouseMove)
      window.removeEventListener('mouseup', handleMouseUp)
    }
  }, [isSelected, isTransitioning])

  return (
    <div 
      ref={containerRef}
      className="background-selector-page"
      onMouseDown={handleMouseDown}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
    >
      <div className="background-selector-title">
        <h1>选择你的背景</h1>
        <p>左右滑动浏览，点击选择</p>
      </div>
      
      <div className="background-carousel-container">
        <div 
          ref={carouselRef}
          className="background-carousel"
          style={{
            transform: `perspective(1000px) rotateY(0deg) translateZ(0)`
          }}
        >
          {backgroundImages.map((imageUrl, index) => {
            const transform = getImageTransform(index)
            return (
              <div
                key={index}
                className={`background-carousel-item ${index === currentIndex ? 'active' : ''}`}
                style={{
                  ...transform,
                  backgroundImage: `url(${imageUrl})`,
                  cursor: isSelected ? 'default' : 'pointer'
                }}
                onClick={() => handleImageClick(index)}
              />
            )
          })}
        </div>
      </div>
      
      {/* 左右箭头（备用方案，如果滑动效果不理想） */}
      {!isSelected && (
        <>
          <button 
            className="carousel-arrow carousel-arrow-left"
            onClick={() => {
              if (!isSelected && !isTransitioning) {
                setCurrentIndex((prev) => (prev > 0 ? prev - 1 : backgroundImages.length - 1))
              }
            }}
          >
            ‹
          </button>
          <button 
            className="carousel-arrow carousel-arrow-right"
            onClick={() => {
              if (!isSelected && !isTransitioning) {
                setCurrentIndex((prev) => (prev < backgroundImages.length - 1 ? prev + 1 : 0))
              }
            }}
          >
            ›
          </button>
        </>
      )}
    </div>
  )
}

export default BackgroundSelector

