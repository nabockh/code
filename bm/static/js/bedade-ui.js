
// Animate Scroll to # links

$(function () {
    $('a[href*=#]:not([href=#])').click(function () {
        if (location.pathname.replace(/^\//, '') == this.pathname.replace(/^\//, '') && location.hostname == this.hostname) {

            var target = $(this.hash);
            target = target.length ? target : $('[name=' + this.hash.slice(1) + ']');
            if (target.length) {
                $('html,body').animate({
                    scrollTop: target.offset().top - 90
                }, 500);
                return false;
            }
        }
    });
});


// End Animate Scroll to # links

// Main Nav behavior on scroll

$( document ).ready(function() {
    var $document = $(document);
    var firstOffset = $('.colorblock#how-it-works').offset().top -90;
    var secondOffset = $('.colorblock#features').offset().top - 90;
    var thirdOffset = $('.colorblock#examples').offset().top - 90;
    var fourthOffset = $('.colorblock#about').offset().top - 90;
    var fifthOffset = $('.colorblock#contact').offset().top - 90;

    $document.on("resize scroll", function () {
        if ($document.scrollTop() < firstOffset) {
            $('.main-nav li#home-link').addClass('active')
            .siblings().removeClass('active');
        }

        if ($document.scrollTop() >= firstOffset) {
            $('.main-nav li#how-link').addClass('active')
            .siblings().removeClass('active');
        }

        if ($document.scrollTop() >= secondOffset - 90) {
             $('.main-nav li#features-link').addClass('active')
            .siblings().removeClass('active');
        }

        if ($document.scrollTop() >= thirdOffset - 90) {
            $('.main-nav li#examples-link').addClass('active')
            .siblings().removeClass('active');
        }

        if ($document.scrollTop() >= fourthOffset - 90) {
            $('.main-nav li#about-link').addClass('active')
            .siblings().removeClass('active');
        }

        if ($document.scrollTop() >= fifthOffset - 180) {
            $('.main-nav li#contacts-link').addClass('active')
            .siblings().removeClass('active');
        }

    });
});



// End Main Nav behavior on scroll