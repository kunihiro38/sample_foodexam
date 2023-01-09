'use strict';

// iframe動画の遅延読み込み
function youtube_defer(){
    var iframes = document.querySelectorAll('.youtube');
    iframes.forEach(function(iframe){
        if(iframe.getAttribute('data-src')) {
            iframe.setAttribute('src',iframe.getAttribute('data-src'));
        }
    });
}
window.addEventListener('load', youtube_defer);
