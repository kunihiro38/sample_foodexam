const swiper = new Swiper(".swiper", {
    // ページネーションが必要なら追加
    pagination: {
      el: ".swiper-pagination"
    },
    // 左右のナビボタン
    navigation: {
      nextEl: ".swiper-button-next",
      prevEl: ".swiper-button-prev"
    },
    // 自動再生
    loop: true,
    autoplay: {
      delya: 3000,
      disableOnInteraction: true
    },
});