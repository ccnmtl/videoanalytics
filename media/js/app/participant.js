/* global Backbone: true, _: true, alert: true, YT: true, onPlayerReady: true */
/* global onPlayerStateChange: true */

(function() {
    window.ParticipantPageView = Backbone.View.extend({
        events: {
            'click a[disabled="disabled"]': 'onClickDisabled',
            'click a.video-back': 'onClickBack',
            'click .nav li[disabled="disabled"] a': 'onClickDisabled',
            'click input[name="submit-page"]': 'onSubmitPage'
        },
        initialize: function(options) {
            _.bindAll(this,
                'onPlayerReady',
                'onPlayerStateChange', 'onYouTubeIframeAPIReady',
                'onClickDisabled', 'onClickBack',
                'isWatching', 'onSubmitPage', 'isFormComplete',
                'recordSecondsViewed');

            this.participant_id = options.participant_id;

            // load the youtube iframe api
            window.onYouTubeIframeAPIReady = this.onYouTubeIframeAPIReady;
            window.onPlayerReady = this.onPlayerReady;
            window.onPlayerStateChange = this.onPlayerStateChange;

            var tag = document.createElement('script');

            // eslint-disable-next-line scanjs-rules/assign_to_src
            tag.src = 'https://www.youtube.com/iframe_api';
            var firstScriptTag = document.getElementsByTagName('script')[0];
            firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
        },
        isFormComplete: function(form) {
            var complete = true;
            var children = jQuery(form).find('input,textarea,select');
            jQuery.each(children, function() {
                if (complete) {
                    if (this.type === 'radio' || this.type === 'checkbox') {
                        // one in the group needs to be checked
                        var selector = 'input[name=' +
                            jQuery(this).attr('name') + ']';
                        complete = jQuery(selector).is(':checked');
                    }
                }
            });
            return complete;
        },
        onSubmitPage: function(evt) {
            var form = jQuery('form[name="page"]')[0];
            if (!this.isFormComplete(form)) {
                alert('Please answer all questions before continuing');
                return false;
            }
            return true;
        },
        onClickDisabled: function(evt) {
            evt.stopImmediatePropagation();
            return false;
        },
        onClickBack: function(evt) {
            window.history.back();
        },
        onPlayerReady: function(event) {
            this.video_id = this.player.getVideoData().video_id;
            this.video_duration = this.player.getDuration();
        },
        onPlayerStateChange: function(event) {
            switch (event.data) {
            case YT.PlayerState.ENDED:
            case YT.PlayerState.PAUSED:
                clearInterval(this.timer);
                delete this.timer;
                this.recordSecondsViewed();
                break;
            case YT.PlayerState.PLAYING:
                jQuery('a, .nav li').attr('disabled', 'disabled');
                this._start = new Date().getTime();
                // eslint-disable-next-line scanjs-rules/call_setInterval
                this.timer = setInterval(this.recordSecondsViewed, 5000);
                    
                break;
            }
        },
        isWatching: function() {
            return this.hasOwnProperty('video_id') &&
                this.video_id.length > 0 &&
                this.hasOwnProperty('video_duration') &&
                this.video_duration > 0 &&
                this.player !== undefined &&
                this.player.getPlayerState() === 1;
        },
        onYouTubeIframeAPIReady: function() {
            this.player = new YT.Player('player', {
                events: {
                    'onReady': onPlayerReady,
                    'onStateChange': onPlayerStateChange
                }
            });
        },
        recordSecondsViewed: function() {
            var self = this;
            if (this._start !== undefined) {
                var end = new Date().getTime();
                var seconds_viewed = (end - this._start) / 1000;

                return jQuery.ajax({
                    type: 'post',
                    url: '/track/',
                    data: {
                        video_id: this.video_id,
                        video_duration: Math.round(this.video_duration),
                        seconds_viewed: Math.round(seconds_viewed)
                    },
                    success: function() {
                        if (self.player.getPlayerState() === 1) {
                            self._start = new Date().getTime();
                        } else {
                            delete self._start;
                            jQuery('a, .nav li').removeAttr('disabled');
                        }
                    },
                    error: function() {
                        this.player.stop();
                        alert('An error occurred.');
                    }
                });
            }
        }
    });
})();
