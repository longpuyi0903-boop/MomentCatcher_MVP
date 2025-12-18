import { useState, useRef, useEffect } from 'react'
import './BackgroundCarousel.css'

/**
 * 3D 传送带背景选择器
 * 修复版本：确保当前选中的图片始终居中显示
 */
const BackgroundCarousel = ({ onSelect, images = [] }) => {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isTransitioning, setIsTransitioning] = useState(false)
  const carouselRef = useRef(null)
  const touchStartX = useRef(0)
  const touchEndX = useRef(0)
  const isDragging = useRef(false)

  // 从图片路径提取文件名（不含扩展名）
  const getImageName = (imagePath) => {
    const fileName = imagePath.split('/').pop() || imagePath
    const nameWithoutExt = fileName.replace(/\.[^/.]+$/, '')
    return nameWithoutExt.toUpperCase()
  }

  // 使用传入的images数组，如果为空则使用空数组（避免加载不存在的文件）
  const allImages = images && images.length > 0 ? images : []
  
  const totalImages = allImages.length
  
  console.log('🎠 BackgroundCarousel 初始化:', { 
    imagesCount: images?.length, 
    allImagesCount: allImages.length,
    currentIndex 
  })

  // 处理滑动切换
  const handleSwipe = (direction) => {
    if (isTransitioning) return
    
    setIsTransitioning(true)
    const newIndex = direction === 'left' 
      ? (currentIndex + 1) % totalImages
      : (currentIndex - 1 + totalImages) % totalImages
    
    setCurrentIndex(newIndex)
    
    setTimeout(() => {
      setIsTransitioning(false)
    }, 400)
  }

  // 触摸事件处理
  const handleTouchStart = (e) => {
    // 如果点击的是图片项，不阻止事件传播
    if (e.target.closest('.background-carousel-item')) {
      return
    }
    touchStartX.current = e.touches[0].clientX
    isDragging.current = true
  }

  const handleTouchMove = (e) => {
    if (!isDragging.current) return
    touchEndX.current = e.touches[0].clientX
  }

  const handleTouchEnd = (e) => {
    if (!isDragging.current) return
    isDragging.current = false
    
    const diff = touchStartX.current - touchEndX.current
    const minSwipeDistance = 50

    // 只有移动距离足够大时才视为滑动，否则视为点击
    if (Math.abs(diff) > minSwipeDistance) {
      e.preventDefault()
      if (diff > 0) {
        handleSwipe('left')
      } else {
        handleSwipe('right')
      }
    }
    
    touchStartX.current = 0
    touchEndX.current = 0
  }

  // 鼠标事件处理（桌面端）
  const handleMouseDown = (e) => {
    // 如果点击的是图片项、导航箭头或指示器，不处理拖动
    if (e.target.closest('.background-carousel-item') || 
        e.target.closest('.carousel-nav-arrow') ||
        e.target.closest('.carousel-indicator')) {
      return
    }
    touchStartX.current = e.clientX
    isDragging.current = true
  }

  const handleMouseMove = (e) => {
    if (!isDragging.current) return
    touchEndX.current = e.clientX
  }

  const handleMouseUp = (e) => {
    if (!isDragging.current) return
    isDragging.current = false
    
    const diff = touchStartX.current - touchEndX.current
    const minSwipeDistance = 50

    // 只有移动距离足够大时才视为滑动，否则视为点击
    if (Math.abs(diff) > minSwipeDistance) {
      if (diff > 0) {
        handleSwipe('left')
      } else {
        handleSwipe('right')
      }
    }
    
    touchStartX.current = 0
    touchEndX.current = 0
  }

  // 点击图片选择
  const handleImageClick = (index, e) => {
    // 检查是否是拖动操作（移动距离大于阈值）
    const wasDragging = isDragging.current && 
                       Math.abs(touchStartX.current - touchEndX.current) > 10
    
    // 如果是拖动操作，不处理点击
    if (wasDragging) {
      return
    }
    
    e.stopPropagation()
    e.preventDefault()
    
    if (isTransitioning) return
    
    // 如果点击的是当前中心图片，直接选择
    if (index === currentIndex) {
      console.log('✅ 选择背景:', allImages[index])
      onSelect(allImages[index])
      return
    }
    
    // 如果点击的不是中心图片，先切换到该图片
    setIsTransitioning(true)
    setCurrentIndex(index)
    
    // 等待切换动画完成后自动选择
    setTimeout(() => {
      setIsTransitioning(false)
      console.log('✅ 切换并选择背景:', allImages[index])
      onSelect(allImages[index])
    }, 400)
  }

  // 计算每张图片的3D变换 - 1:1 复刻参考代码
  const getImageStyle = (index) => {
    // 计算相对于当前选中图片的偏移
    const offset = index - currentIndex
    const isCenter = offset === 0
    const absOffset = Math.abs(offset)
    
    // 只显示附近的项（参考代码：if (absOffset > 2) return null）
    if (absOffset > 2) {
      return { display: 'none' }
    }
    
    // 1:1 复刻参考代码的3D变换逻辑
    const rotateY = offset * 45 // Basic 3D Ring Logic
    const translateZ = isCenter ? 150 : -200 - absOffset * 100
    const opacity = isCenter ? 1 : 0.3 / absOffset
    const scale = isCenter ? 1 : 0.8
    const blur = isCenter ? 'blur(0px)' : 'blur(4px)'
    const zIndex = 10 - absOffset
    
    return {
      transform: `rotateY(${rotateY}deg) translateZ(${translateZ}px) scale(${scale})`,
      opacity: opacity,
      filter: blur,
      zIndex: zIndex
    }
  }

  // 键盘导航
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'ArrowLeft') {
        handleSwipe('right')
      } else if (e.key === 'ArrowRight') {
        handleSwipe('left')
      } else if (e.key === 'Enter') {
        onSelect(allImages[currentIndex])
      }
    }
    
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [currentIndex, allImages, onSelect])

  return (
    <div 
      className="background-carousel-overlay"
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      onClick={(e) => {
        // 如果点击的是背景区域（不是图片、箭头或指示器），且当前有中心图片，选择它
        if (!e.target.closest('.background-carousel-item') &&
            !e.target.closest('.carousel-nav-arrow') &&
            !e.target.closest('.carousel-indicator') &&
            !isDragging.current &&
            !isTransitioning) {
          console.log('✅ 点击背景区域，选择当前中心图片')
          onSelect(allImages[currentIndex])
        }
      }}
    >
      {/* 标题 - 1:1 复刻参考代码样式 */}
      <div className="carousel-title">
        <h2 className="carousel-title-subtitle">Quantum Library</h2>
        <h1 className="carousel-title-main">Select Your Destination</h1>
      </div>
      
      <div className="background-carousel-container" ref={carouselRef}>
        <div className="background-carousel-scene">
          {allImages.map((image, index) => {
            const style = getImageStyle(index)
            const isCenter = index === currentIndex
            
            // 如果超出显示范围，不渲染
            if (style.display === 'none') {
              return null
            }
            
            return (
              <div
                key={`${image}-${index}`}
                className={`background-carousel-item group ${isCenter ? 'center' : ''}`}
                style={{
                  ...style,
                  transition: isTransitioning ? 'all 1s ease-out' : 'none',
                  cursor: 'pointer'
                }}
                onClick={(e) => handleImageClick(index, e)}
              >
                <div className={`relative w-full h-full rounded-sm overflow-hidden border transition-all duration-700 ${isCenter ? 'border-white/30 shadow-[0_0_50px_rgba(255,255,255,0.05)]' : 'border-white/10'}`}>
                <img 
                  src={image} 
                  alt={`Background ${index + 1}`}
                  className="background-carousel-image"
                  draggable={false}
                />
                  {/* 渐变遮罩 - 1:1 复刻参考代码 */}
                  <div className="carousel-image-overlay"></div>
                  
                  {/* 中心图片信息覆盖层 - 1:1 复刻参考代码 */}
                {isCenter && (
                    <div className="carousel-item-info">
                      <div className="carousel-item-id">// {index + 1}</div>
                      <div className="carousel-item-name">{getImageName(image)}</div>
                    </div>
                )}
                </div>
              </div>
            )
          })}
      </div>
      
        {/* 导航箭头 - 1:1 复刻参考代码（放在container内部，相对于容器定位） */}
      <button 
        className="carousel-nav-arrow carousel-nav-left"
        onClick={(e) => {
          e.stopPropagation()
          handleSwipe('right')
        }}
      >
          <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={0.5} d="M15 19l-7-7 7-7" />
          </svg>
      </button>
      <button 
        className="carousel-nav-arrow carousel-nav-right"
        onClick={(e) => {
          e.stopPropagation()
          handleSwipe('left')
        }}
      >
          <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={0.5} d="M9 5l7 7-7 7" />
          </svg>
      </button>
      </div>
      
      {/* 指示器 - 1:1 复刻参考代码样式 */}
      <div className="carousel-indicators">
        {allImages.map((_, index) => (
          <div
            key={index}
            className={`carousel-indicator ${index === currentIndex ? 'active' : ''}`}
            onClick={(e) => {
              e.stopPropagation()
              if (!isTransitioning && index !== currentIndex) {
                setIsTransitioning(true)
                setCurrentIndex(index)
                setTimeout(() => setIsTransitioning(false), 400)
              }
            }}
          />
        ))}
      </div>
      
      {/* 底部提示文字 - 1:1 复刻参考代码 */}
      <div className="carousel-hint">
        CLICK CENTER FRAGMENT TO CONFIRM COORDINATES
      </div>
    </div>
  )
}

export default BackgroundCarousel
