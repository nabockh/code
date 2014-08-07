google.load("visualization", "1", {packages:["corechart"]});
// google.setOnLoadCallback(drawChart);
        
$(function () {
    var sectionStateChangeStep1 = function() {
        var selectedStep1 = $('#id_0-question_type').find('option:selected').val();
            if (selectedStep1 > 2) {
                $('#units_maxDecimals').show();
                $('#answer_options').hide();
            }
            else {
                $('#answer_options').show();
                $('#units_maxDecimals').hide();
            }
    };

    var sectionStateChangeStep3 = function() {
        var selectedStep3 = $('#id_2-question_type').find('option:selected').val();
            if (selectedStep3 > 2) {
                $('#units_maxDecimals_step3').show();
                $('#answer_options_step3').hide();
            }
            else {
                $('#answer_options_step3').show();
                $('#units_maxDecimals_step3').hide();
            }
    };

    var chartTypeChange = function() {
        var chartTypeChange = $('#id_Benchmark_Results').find('option:selected').val();
            if (chartTypeChange == "Pie") {
                $('#donutChartHolder').show();
                $('#columnChartHolder').hide();
                $('#bellcurveChartHolder').hide();
                $('#lineChartHolder').hide();
            }

            if (chartTypeChange == "Column") {
                $('#donutChartHolder').hide();
                $('#columnChartHolder').show();
                $('#bellcurveChartHolder').hide();
                $('#lineChartHolder').hide();
            }

            if (chartTypeChange == "Bell_Curve") {
                $('#donutChartHolder').hide();
                $('#columnChartHolder').hide();
                $('#bellcurveChartHolder').show();
                $('#lineChartHolder').hide();
            }

            if (chartTypeChange == "Line") {
                $('#donutChartHolder').hide();
                $('#columnChartHolder').hide();
                $('#bellcurveChartHolder').hide();
                $('#lineChartHolder').show();
            }
    };

    var statisticViewChange = function() {
        var statisticViewChange = $('#id_Contributor_Data').find('option:selected').val();
            if (statisticViewChange == "Role") {
                $('#roleStats').show();
                $('#industryStats').hide();
                $('#countryStats').hide();
                $('#geoStats').hide();
            }

            if (statisticViewChange == "Geo") {
                $('#roleStats').hide();
                $('#industryStats').hide();
                $('#countryStats').hide();
                $('#geoStats').show();
            }

            if (statisticViewChange == "Country") {
                $('#roleStats').hide();
                $('#industryStats').hide();
                $('#countryStats').show();
                $('#geoStats').hide();
            }

            if (statisticViewChange == "Industry") {
                $('#roleStats').hide();
                $('#industryStats').show();
                $('#countryStats').hide();
                $('#geoStats').hide();
            }
    };

    sectionStateChangeStep1();
    sectionStateChangeStep3();
    statisticViewChange();
    chartTypeChange();
    

    $( "#id_0-question_type" ).on('change', sectionStateChangeStep1);
    $( "#id_2-question_type" ).on('change', sectionStateChangeStep3);
    $( "#id_Contributor_Data" ).on('change', statisticViewChange);
    $( "#id_Benchmark_Results" ).on('change', chartTypeChange);

    $('#myRecentBenchmarks .item:not(:first-child)').removeClass('active');
    $('#popularComunityBenchmarks .item:not(:first-child)').removeClass('active');
    
    $( ".dashboard-progress-block .progress .progress-bar" ).each(function() {
        var dataProgress = $(this).attr('aria-valuenow');
        if (dataProgress <= 33) {
            $(this).parents('.dashboard-progress-block').addClass('one-third');
        }

        else if (dataProgress >= 66) {
            $(this).parents('.dashboard-progress-block').addClass('three-third');
        }

        else {
            $(this).parents('.dashboard-progress-block').addClass('two-third');   
        }
    });    
});




$(function () {

    setTimeout(function () {
            $('.preloader').fadeOut( "slow" );
    }, 1000);

    // Example Blocks

    $('.example-block').on('click', function(e) {
       $(this).addClass('active').removeClass('closed').siblings().addClass('closed').removeClass('active');
       e.stopPropagation();
    });

    $("html").click(function() {
        $(".example-block").removeClass('closed active');
    });

    // Tooltips

    $('.add_help').on('click', function() {
       $(this).children('.add_help_inner').toggleClass('visible');
    });

    // Rating Functionality

    $('.rating').on('click', '[data-score]', function() {
        var csrf = document.cookie.match(/csrftoken=([\w]+)/);
        var request = $.post(window.location.pathname, {'csrfmiddlewaretoken' : csrf? csrf[1] : null,
                                          'rate' : $(this).attr('data-score')});
        request.done(function (response){
            $('.color-grey').html("(" + response + ")");
            var rate_percentage =  response/5*100 + '%';
            $('.fill-value').css({ 'width': rate_percentage});
        });
    });

    // Ranking Benchmark functionality

    $( "#answerSortable" ).sortable({
      placeholder: "ui-state-highlight"
    });
    $( "#answerSortable" ).disableSelection();

    $( "#answerSortable" ).on( "sortupdate", function( event, ui ) {
        $(this).find('li input[type=hidden]').each(function(index){
            $(this).val(index);
        });
    } );

    // Layout JS

    $('.collapse').collapse({
        toggle: false
    });

    

    $('.carousel').carousel({interval: false});
    $(document).on('mouseleave', '.carousel', function() {
        $(this).carousel('pause');
    });

    // Benchmark Creation Tabs

    $('#searchTabs a, .tab-switcher').click(function (e) {
      e.preventDefault();
      e.stopPropagation();
      $(this).tab('show');
    });

    $('.tab-switcher').click(function (e) {
        $('.search .tabulation .nav-tabs li.tab-recommended').tab('show').addClass('active');
        e.stopPropagation();
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
                $(this).parents('.col-md-2').siblings('.col-md-2').children('input[type="checkbox"]').removeAttr('checked');
            }
        }
    });

    $('.choose-checkbox').change(function() {
        if ($(this).is(':checked') == false) {
            if ($(this).parents('.col-md-2').siblings('.col-md-2').children('input[type="checkbox"]').is(':checked') == true) {
                $(this).parents('.col-md-2').siblings('.col-md-2').children('input[type="checkbox"]').removeAttr('checked');
            }
        }
    });

    $('span.deselect-btn').click(function () {
        var id = $(this).parents('.single-contact').attr('data-contact-id');
        $('#results .single-contact[data-contact-id='+id+']').find('.choose-checkbox, .share-checkbox').removeAttr('checked');
        $('#selected .single-contact[data-contact-id='+id+']').find('.choose-checkbox, .share-checkbox').removeAttr('checked').end().fadeOut(500, function(){ $(this).remove();});
        $('#recommended .single-contact[data-contact-id='+id+']').find('.choose-checkbox, .share-checkbox').removeAttr('checked');
        $('#step3Selected .single-contact[data-contact-id='+id+']').find('.choose-checkbox, .share-checkbox').removeAttr('checked').end().fadeOut(500, function(){ $(this).remove();});
    });

    $('.share-checkbox').on('change', function() {
        var id = $(this).parents('.single-contact').attr('data-contact-id');
        if ($(this).is(':checked') == false) {
            $('#results .single-contact[data-contact-id='+id+']').find('.share-checkbox').prop('checked', false);
            $('#selected .single-contact[data-contact-id='+id+']').find('.share-checkbox').prop('checked', false);
            $('#recommended .single-contact[data-contact-id='+id+']').find('.share-checkbox').prop('checked', false);
            $('#step3Selected .single-contact[data-contact-id='+id+']').find('.share-checkbox').prop('checked', false);
        }
        else {
            $('#results .single-contact[data-contact-id='+id+']').find('.share-checkbox').prop('checked', true);
            $('#selected .single-contact[data-contact-id='+id+']').find('.share-checkbox').prop('checked', true);
            $('#recommended .single-contact[data-contact-id='+id+']').find('.share-checkbox').prop('checked', true);
            $('#step3Selected .single-contact[data-contact-id='+id+']').find('.share-checkbox').prop('checked', true);
        }
    });

});


// Animate Scroll to # links

$(function () {
    $('.main-nav a[href*=#]:not([href=#])').click(function () {
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

// Script for Ajax Email Preview on 3-rd step of BM creation
$(document).off("click","label.btn-primary");
$(document).on("click","label.btn-primary",function(){
    var csrf = document.cookie.match(/csrftoken=([\w]+)/);
    var data = $('.styled-form').serialize();
    var request = $.ajax({
            url: window.location.pathname,
            type: 'post',
            'csrfmiddlewaretoken' : csrf? csrf[1] : null,
            'data': data
    });

    // callback handler that will be called on success
        request.done(function (response, textStatus, jqXHR){
            $('.modal-body').html(response);
            // log a message to the console
            console.log(response);
        });

        // callback handler that will be called on failure
        request.fail(function (jqXHR, textStatus, errorThrown){
            // log the error to the console
            console.error(
                "The following error occured: "+
                textStatus, errorThrown
            );
        });

    });

// Ajax post on Contact Form

$(document).off("submit","form#contact_form");
$(document).on("submit","form#contact_form", function(e){
        e.preventDefault();
        var csrf = document.cookie.match(/csrftoken=([\w]+)/);
        console.log(csrf? csrf[1] : null);
        console.log("submit start");
         $.ajax({
            type: 'post',
            url: $(this).attr('action'),
            'csrfmiddlewaretoken' : csrf? csrf[1] : null,
            data: $('#contact_form').serialize(),
            success: function(){
                $('#support').modal('toggle');
                $("form#contact_form")[0].reset();
            }

            });
    });

// Validation of Contract Forms

$(function () {

    $("#contact_form").validate({ // initialize the plugin

        rules: {
            email: {
                required: true,
                email: true
            },
            first_name: {
                required: true
            },
            last_name: {
                required: true
            },
            comment: {
                minlength: 5,
                required: true
            }
        }
    });
});


// DataTable for Search and History page

$(function() {
    if ( (document.getElementsByClassName('benchmark')).length > 0 ) {
        $('.results').dataTable({
            Info: false,
            bPaginate: true
        });

    }
});


// Main Nav behavior on scroll

$( document ).ready(function() {
    var $document = $(document);
    var navOffset = $('.user-nav').offset().top;

    $document.on("scroll", function () {
        if ($document.scrollTop() > navOffset) {
            $('body').addClass('fixed-navs')
        }

        else {
            $('body').removeClass('fixed-navs')
        }
    });
});
