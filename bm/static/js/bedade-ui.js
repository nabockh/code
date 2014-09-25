google.load("visualization", "1", {packages:["corechart"]});
// google.setOnLoadCallback(drawChart);
        
$(function () {
    var sectionStateChangeStep1 = function() {
        var selectedStep1 = $('#id_0-question_type').find('option:selected').val();
            if (selectedStep1 > 2) {
                $('#units_maxDecimals').show();
                $('#answer_options').hide();
                $('#units_maxDecimals').next('hr').show();
            }
            else {
                $('#answer_options').show();
                $('#units_maxDecimals').hide();
                $('#units_maxDecimals').next('hr').show();
            }
            if (selectedStep1 == 4) {
                $('#units_maxDecimals').hide();
                $('#answer_options').hide();
                $('#units_maxDecimals').next('hr').hide();
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

    $('.carousel-inner .item:not(:first-child)').removeClass('active');

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
    $(".show-terms").click(function() {
        $(".terms-container").toggleClass('terms-show');
    });

    // Tooltips

    $('.add_help').on('click', function(e) {
       $(this).children('.add_help_inner').addClass('visible');
       e.stopPropagation();
    });

    $("html").click(function() {
        $(".add_help_inner").removeClass('visible');
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

    // $('.single-contact input[type="checkbox"]').change(function() {
    //     if ($('.single-contact input[type="checkbox"]:checked').length > 0) {
    //         $(this).parents('.single-contact').addClass('active');
    //     }
    //     else {
    //         $(this).parents('.single-contact').removeClass('active');
    //     }
    // });
    
    
    $('*[data-modal-close="true"]').click(function () {
        $(this).parents('.smallModal').fadeOut(500);
    });

    $('#rec_btn').click(function () {
        $( ".char-fillter li.filter-all" ).trigger( "click" );
        $('#recommendedContactList').show();
        $('#searchContactList').hide();
    });


    $('.share-checkbox').change(function() {
        if ($(this).is(':checked') === true) {
            if ($(this).parents('.col-md-1').siblings('.col-md-1').children('input[type="checkbox"]').is(':checked') === false) {
                $(this).parents('.col-md-1').siblings('.col-md-1').children('input[type="checkbox"]').removeAttr('checked');
            }
        }
    });

    $('.choose-checkbox').change(function() {
        if ($(this).is(':checked') === false) {
            if ($(this).parents('.col-md-4').siblings('.col-md-4').children('input[type="checkbox"]').is(':checked') === true) {
                $(this).parents('.col-md-4').siblings('.col-md-4').children('input[type="checkbox"]').removeAttr('checked');
            }
        }
    });

    $('span.deselect-btn').click(function () {
        var id = $(this).parents('.single-contact').attr('data-contact-id');
        $('#searchContactList .single-contact[data-contact-id='+id+']').find('.choose-checkbox, .share-checkbox').removeAttr('checked');
        $('#selectedContactList .single-contact[data-contact-id='+id+']').find('.choose-checkbox, .share-checkbox').removeAttr('checked').end().fadeOut(500, function(){ $(this).remove();});
        $('#recommendedContactList .single-contact[data-contact-id='+id+']').find('.choose-checkbox, .share-checkbox').removeAttr('checked');
        $('#step3Selected .single-contact[data-contact-id='+id+']').find('.deChecker').attr('value', '').end().fadeOut(500, function(){ $(this).remove();});
    });


    $('.col-md-8.lined-left.margined .share-checkbox').on('click', function() {
        var id = $(this).parents('.single-contact').attr('data-contact-id');
        if ($(this).is(':checked') === false) {
            $('#searchContactList .single-contact[data-contact-id='+id+']').find('.share-checkbox').prop('checked', false);
            $('#selectedContactList .single-contact[data-contact-id='+id+']').find('.share-checkbox').prop('checked', false);
            $('#recommendedContactList .single-contact[data-contact-id='+id+']').find('.share-checkbox').prop('checked', false);
            $('#step3Selected .single-contact[data-contact-id='+id+']').find('.share-checkbox').prop('checked', false);
        }
        else {
            $('#searchContactList .single-contact[data-contact-id='+id+']').find('.share-checkbox').prop('checked', true);
            $('#selectedContactList .single-contact[data-contact-id='+id+']').find('.share-checkbox').prop('checked', true);
            $('#recommendedContactList .single-contact[data-contact-id='+id+']').find('.share-checkbox').prop('checked', true);
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
$(document).off("click","label.btn-primary[data-target='#preview']");
$(document).on("click","label.btn-primary[data-target='#preview']",function(){
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
            $('#preview .modal-body').html(response);
            // log a message to the console
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
     $.ajax({
        type: 'post',
        url: $(this).attr('action'),
        'csrfmiddlewaretoken' : csrf? csrf[1] : null,
        data: $('#contact_form').serialize(),
        success: function(data, textStatus, xhr){
            $('#support').modal('toggle');
            $("form#contact_form")[0].reset();
            $('#contact_submitted').modal('toggle');
                setTimeout(function() {
                $('#contact_submitted').modal('hide');
            }, 1000);
        }
    });
});

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

$(function () {

    $("#invite_colleague_form").validate({ // initialize the plugin

        rules: {
            colleague_email: {
                required: true,
                email: true
            }
        }
    });
});

$(function () {

    $("#beta_invitation_form").validate({ // initialize the plugin

        rules: {
            "invite-email": {
                email: true
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

//Selectbox customize
function select_prepare() {
    $('select').each(function(){
        var $select = $(this);
        var width = $select.parents('div:eq(0)').width();
        var param_search = 100;
        if($(this).parent('div').hasClass('title-header')){
            width = 150;
            param_search = -1;
        }
        $select.prev('.select2-container').remove();
        $select2 = $select.removeAttr('style').css('width', width).select2({minimumResultsForSearch: param_search});
        $select2.on("select2-open", function(){$('.select2-offscreen > .select2-input').blur();}); // Workaround not to show cursor on iPad
        if($select.parents('#units_maxDecimals, #units_maxDecimals_step3').length){
            $('#units_maxDecimals select, #units_maxDecimals_step3 select').each(function(){
               $(this).next('.units-custom').val($(this).val());
               $(this).on("change", function(e) {
                   $(this).next('.units-custom').val($(this).val());
               });
            });
        }
    });
}


// Main Nav behavior on scroll

$( document ).ready(function() {
    var $document = $(document);
    var navOffset = $('.user-nav').offset().top;

    $document.on("scroll", function () {
        if ($document.scrollTop() > navOffset) {
            $('body').addClass('fixed-navs');
        }

        else {
            $('body').removeClass('fixed-navs');
        }
    });

    select_prepare();
    if ($('.carousel-inner').length){
        if ($('.carousel-inner .item').length < 2){
            $('.recent-benchmark-controls').hide();
        }
    }

    // Benchmark answer options

    if ($('body .answer_options_area').length){
        if($(".answer_options_area textarea").val() !== ""){
            $('.answer_options_inputs .col-md-4:not(:last-child)').remove();
        }
        var breaks = $(".answer_options_area textarea").val().split('\n');
        var newLines = "";
        for(var i = 0; i < breaks.length; i ++){
            newLine = breaks[i];
            var trim = newLine.replace(/ /g,'');
            if(trim !== ""){
                $('.answer_options_inputs .col-md-4:last-child').before('<div class="col-md-4"><input type="text" maxlength="45" value="' + newLine + '"></div>');
            }
        }
    }
    var txt = $(".answer_options_area textarea");
    $('.benchmark-creation form').bind('submit','',function(){
            txt.val('');
        if ($('#answer_options').css('display') != 'none' || $('#answer_options_step3').css('display') != 'none'){
            $('.answer_options_inputs input[type="text"]').each(function(){
                var input_val = $(this).val();
                var trim = input_val.replace(/ /g,'');
                if(trim !== ""){
                    txt.val( txt.val() + input_val + "\n");
                }
            });
        }
        if($("#units_maxDecimals .units-custom, #units_maxDecimals_step3 .units-custom").val() !== ""){
            var $units_select = $(this).closest('form').find('select#id_0-units');
            var $units_select_form = $(this).closest('form').find('select#id_0-units').prev('.select2-container').find('.select2-chosen');
            var units_input_val = $(this).closest('form').find('.units-custom').val();
            $units_select_form.text(units_input_val);
            $units_select.find('option[selected="selected"]').removeAttr('selected');
            $units_select.append('<option selected="selected" value="' + units_input_val + '">' + units_input_val + '</option>');
        }
    });
    $(document).on("click",".answer_options_inputs .answer_options_add",function(){
        $('.answer_options_inputs .col-md-4:last-child').before('<div class="col-md-4"><input type="text" value="" maxlength="45" class="ui-new-option"></div>');
        $('.ui-new-option').focus().removeAttr('class');
    });

    if ($('#from1_flag').length > 0) {
        $('#recommendedContactList').show();
        $('#searchContactList').hide();
    } else {
        $('#recommendedContactList').hide();
        $('#searchContactList').show();
    }

    $('#recommendedContactList .add-contact-btn, #searchContactList .add-contact-btn').on('click',function(){
        if(!$(this).attr('disabled')){
            var $this_parent = $(this).closest('.single-contact');
            var this_id = $this_parent.attr('data-contact-id');
            var this_name = $this_parent.find('label:not(.btn)').text();
            var this_title = $this_parent.find('p:not(.grey)').text();
            var allowed = $this_parent.find('.share-checkbox:checked').length;
            var allowed_target = "";
            if(allowed == 1){
                allowed_target = "checked";
            }
            var clone_block = [
                '<div data-contact-id="' + this_id + '" class="single-contact">',
                    '<div class="row">',
                        '<div class="col-md-10 col-xs-10">',
                            '<div class="row">',
                                '<div class="col-md-12">',
                                    '<label>' + this_name + '</label>',
                                    '<p title="' + this_title + '">' + this_title + '</p>',
                                '</div>',
                                '<div class="col-md-12 col-xs-12 selected-check">',
                                    '<input type="checkbox" name="1-selected-' + this_id + '-secondary" id="id_1-selected-' + this_id + '-secondary" class="share-checkbox" ' + allowed_target + '>',
                                    '<label for="id_1-selected-' + this_id + '-secondary" class="nobold">Allow Forwarding</label>',
                                '</div>',
                            '</div>',
                        '</div>',
                        '<div class="col-md-2 col-xs-2 text-center">',
                            '<span class="hidden"><input type="checkbox" name="1-selected-' + this_id + '-invite" id="id_1-selected-' + this_id + '-invite" class="choose-checkbox" checked="checked"></span>',
                            '<span class="deselect-btn"><i class="fa fa-times"></i></span>',
                        '</div>',
                    '</div>',
                '</div>',
            ].join("\n");
            $('#selectedContactList .mCSB_container').append(clone_block);
            $(this).attr('disabled', 'disabled');
            $('#selectedContactList .deselect-btn').click( function(){
                var $this_parent = $(this).closest('.single-contact');
                var this_id = $this_parent.attr('data-contact-id');
                $target_block = $('#recommendedContactList, #searchContactList').find('.single-contact[data-contact-id="' + this_id + '"]');
                $target_block.find('.add-contact-btn').removeAttr('disabled');
                $this_parent.remove();
                $target_block.find('.choose-checkbox, .share-checkbox').removeAttr('checked');
               
            });
        }
        $('#selectedContactList .share-checkbox').on('click',function() {
            var $this_parent = $(this).closest('.single-contact');
            var this_id = $this_parent.attr('data-contact-id');
            $target_checkbox = $('.col-md-8.lined-left.margined').find('.single-contact[data-contact-id="' + this_id + '"]').find('.share-checkbox');
            if ($(this)[0].checked  === true) {
                $target_checkbox.removeAttr('checked').prop('checked', true);
            }
            else {
                $target_checkbox.removeAttr('checked').prop('checked', false);
            }
        });
    });

    $('#selectedContactList .share-checkbox').on('click',function() {
        var $this_parent = $(this).closest('.single-contact');
        var this_id = $this_parent.attr('data-contact-id');
        $target_checkbox = $('.col-md-8.lined-left.margined').find('.single-contact[data-contact-id="' + this_id + '"]').find('.share-checkbox');
        if ($(this)[0].checked  === true) {
            $target_checkbox.removeAttr('checked').prop('checked', true);
        }
        else {
            $target_checkbox.removeAttr('checked').prop('checked', false);
        }
    });

    $('#selectedContactList .single-contact').each(function(){
        var this_id = $(this).attr('data-contact-id');
        $target_block = $('#recommendedContactList, #searchContactList').find('.single-contact[data-contact-id="' + this_id + '"]');
        $target_block.find('.add-contact-btn').attr('disabled', 'disabled');
        
    });
    $('#selectedContactList .deselect-btn').click( function(){
        var $this_parent = $(this).closest('.single-contact');
        var this_id = $this_parent.attr('data-contact-id');
        $target_block = $('#recommendedContactList, #searchContactList').find('.single-contact[data-contact-id="' + this_id + '"]');
        $target_block.find('.add-contact-btn').removeAttr('disabled');
        $this_parent.remove();
    });
    $('.add-all').click( function(){
        $(this).closest('.title-header').next('.contact-results').find('.add-contact-btn:visible').click();
    });
    $('.tips .remove-all').click( function(){
        $(this).closest('.tips').find('.deselect-btn').click();
    });

});
$(window).on('resize', function(){
    select_prepare();
});
$(document).ajaxStop(function() {
});


$( document ).ready(function(){
    $( "#preview" ).on('shown.bs.modal', function() {
        $( '.save-button' ).on('click', function() {
            $('#email_body').text($('#default_text').text());
            $( "#preview" ).modal('hide');
            $('#default_text').css('background-color', '#F5F5F5');
        });
    });

    $(".char-fillter li").click(function() {
        var filter_char = $(this).text();
        if($(this).hasClass('filter-all')){
            $("#searchContactList .single-contact, #recommendedContactList .single-contact").removeClass('char-fillter-apply char-filltered');
        }
        else{
            $("#searchContactList .single-contact, #recommendedContactList .single-contact").each(function() {
                $(this).removeClass('char-fillter-apply char-filltered').addClass('char-fillter-apply');
                var str = $('.col-md-6.col-xs-6 label:first-child', this).text().split(' ').pop()[0].substring(0, 1);
                if(str === filter_char){
                    $(this).addClass('char-filltered');
                }
            });
        }
    });
});




    


