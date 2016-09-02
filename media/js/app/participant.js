(function() {
    window.ParticipantPageView = Backbone.View.extend({
        events: {
            'click a[disabled="disabled"]': 'onClickDisabled',
            'click .nav li[disabled="disabled"] a': 'onClickDisabled'
        },
        initialize: function(options) {
            _.bindAll(this,
                      'onPlayerReady',
                      'onPlayerStateChange',
                      'onYouTubeIframeAPIReady',
                      'isWatching',
                      'recordSecondsViewed');

            var self = this;
            this.participant_id = options.participant_id;

            // load the youtube iframe api
            window.onYouTubeIframeAPIReady = this.onYouTubeIframeAPIReady;
            window.onPlayerReady = this.onPlayerReady;
            window.onPlayerStateChange = this.onPlayerStateChange;

            var tag = document.createElement('script');
            tag.src = 'https://www.youtube.com/iframe_api';
            var firstScriptTag = document.getElementsByTagName('script')[0];
            firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
        },
        onClickDisabled: function(evt) {
            evt.preventDefault();
            return false;
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
