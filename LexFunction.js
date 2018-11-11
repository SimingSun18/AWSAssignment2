    exports.handler = (event, context, callback) => {
        var result;
    var AWS = require('aws-sdk');
    AWS.config.region = 'us-west-2';
    var lexUserId = 'DiningChatBot';
    var lexruntime = new AWS.LexRuntime();
    var text = event.messages[0].unstructured.text;
    console.log("test text is "+text);
    var params = {
            botAlias: "$LATEST",
            botName: "DiningChatBot",
            inputText: text,
            userId: lexUserId,
            sessionAttributes: {}
        };
    console.log("start");
    lexruntime.postText(params, function(err, data) {
        if (err) {
            console.log(err, err.stack); // an error occurred
            twimlResponse.message('Sorry, we ran into a problem at our end.');
            callback(err, "failed");
        } else {
            console.log(data); // got something back from Amazon Lex
            return_info = {"messages": [{"type": "string","unstructured": {"id": lexUserId,"text": data.message,"timestamp": String(Date.now())}}]};
            console.log(data.message);
            context.succeed(return_info);
        }
    });
    };

