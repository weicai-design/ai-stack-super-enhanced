/**
 * 调试工具
 * 用于诊断按钮无法点击的问题
 */

(function() {
    console.log('🔍 调试工具加载...');
    
    // 等待DOM加载
    function debugButtons() {
        console.log('🔍 开始调试按钮状态...');
        
        // 检查所有按钮
        const buttons = {
            'play-btn': document.getElementById('play-btn'),
            'square-btn': document.getElementById('square-btn'),
            'voice-btn': document.getElementById('voice-btn'),
            'file-btn': document.getElementById('file-btn'),
            'search-icon-btn': document.getElementById('search-icon-btn'),
            'chat-input': document.getElementById('chat-input'),
            'model-selector': document.getElementById('model-selector')
        };
        
        console.log('📋 按钮状态检查:');
        for (const [id, element] of Object.entries(buttons)) {
            if (element) {
                const styles = window.getComputedStyle(element);
                console.log(`✅ ${id}:`, {
                    display: styles.display,
                    visibility: styles.visibility,
                    pointerEvents: styles.pointerEvents,
                    zIndex: styles.zIndex,
                    position: styles.position,
                    cursor: styles.cursor,
                    opacity: styles.opacity
                });
                
                // 强制设置可点击
                element.style.setProperty('pointer-events', 'auto', 'important');
                element.style.setProperty('cursor', 'pointer', 'important');
                element.style.setProperty('user-select', 'none', 'important');
                element.style.setProperty('z-index', '1000', 'important');
                
                // 测试点击
                element.addEventListener('click', function(e) {
                    console.log(`✅✅✅ ${id} 被点击了！`, e);
                }, { once: true });
            } else {
                console.error(`❌ ${id} 元素不存在`);
            }
        }
        
        // 检查导航项
        const navItems = document.querySelectorAll('.nav-item');
        console.log(`📋 找到 ${navItems.length} 个导航项`);
        navItems.forEach((item, index) => {
            const styles = window.getComputedStyle(item);
            console.log(`导航项 ${index}:`, {
                pointerEvents: styles.pointerEvents,
                cursor: styles.cursor
            });
            
            // 强制设置可点击
            item.style.setProperty('pointer-events', 'auto', 'important');
            item.style.setProperty('cursor', 'pointer', 'important');
            item.style.setProperty('z-index', '1000', 'important');
        });
        
        // 检查是否有覆盖层
        const overlays = document.querySelectorAll('[style*="position: fixed"], [style*="position: absolute"]');
        console.log(`📋 找到 ${overlays.length} 个可能的覆盖层`);
        overlays.forEach((overlay, index) => {
            const styles = window.getComputedStyle(overlay);
            if (parseInt(styles.zIndex) > 1000) {
                console.warn(`⚠️ 高z-index覆盖层 ${index}:`, {
                    zIndex: styles.zIndex,
                    pointerEvents: styles.pointerEvents,
                    element: overlay
                });
            }
        });
        
        console.log('✅ 调试完成');
    }
    
    // 立即执行
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', debugButtons);
    } else {
        setTimeout(debugButtons, 500);
    }
    
    // 5秒后再次检查
    setTimeout(debugButtons, 5000);
})();

