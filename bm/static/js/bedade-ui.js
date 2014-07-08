    
$(function () {
    var sectionStateChange = function() {
        var selected = $('#id_0-question_type').find('option:selected').val();
            if (selected > 2) {
                $('#units_maxDecimals').show();
                $('#answer_options').hide();
            }
            else {
                $('#answer_options').show();
                $('#units_maxDecimals').hide();
            }
    };
    sectionStateChange();
    $( "#id_0-question_type" ).on('change', sectionStateChange);
});



$(function () {

    // Becnhmark Creation Tabs

    $('#searchTabs a, .tab-switcher').click(function (e) {
      e.preventDefault()
      $(this).tab('show');
    });

    $('.tab-switcher').click(function (e) {
        $('.search .tabulation .nav-tabs li.tab-recommended').tab('show').addClass('active');
    });

    // Becnhmark Creation Checkboxes

    $('.single-contact input[type="checkbox"]').change(function() {
        if ($('.single-contact input[type="checkbox"]:checked').length > 0) {
            $(this).parents('.single-contact').addClass('active');
        }
        else {
            $(this).parents('.single-contact').removeClass('active');
        }
    });

    $('.share-checkbox').change(function() {
        if ($(this).is(':checked') == true) {
            if ($(this).parents('.col-md-2').siblings('.col-md-2').children('input[type="checkbox"]').is(':checked') == false) {
                $(this).parents('.col-md-2').siblings('.col-md-2').children('input[type="checkbox"]').trigger('click');
            }
        }
    });

    $('.choose-checkbox').change(function() {
        if ($(this).is(':checked') == false) {
            if ($(this).parents('.col-md-2').siblings('.col-md-2').children('input[type="checkbox"]').is(':checked') == true) {
                $(this).parents('.col-md-2').siblings('.col-md-2').children('input[type="checkbox"]').trigger('click');
            }
        }
    });
});



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

    $document.on("scroll", function () {
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
        console.clear();
    });

});



// End Main Nav behavior on scroll
