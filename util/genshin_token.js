const main = () => {
    const domain = (new URL(location.href)).hostname.replace("www.", "").replace("act.", "");

    if (domain != "hoyolab.com") {
        if(confirm("HoYoLABのページにアクセスし直してからこのスクリプトを実行してください。\nHoyoLABにアクセスしますか？\nスクリプトは実行し直す必要があります。")){
            location.href = "https://www.hoyolab.com/";
            return;
        }
        return;
    }

    const cookies = document.cookie.split("; ");
    var ltuid = "";
    var ltoken = "";

    cookies.forEach(function(cookie){
        data = cookie.split("=");
        if (data[0] == "ltuid"){
            ltuid = data[1];
        } else if (data[0] == "ltoken"){
            ltoken = data[1];
        }
    });

    if (ltuid == "") {
        alert("ログインし直してください。\nHoYoLAB UIDが見つかりませんでした。");
        return;
    } else if (ltoken == "") {
        alert("ログインし直してください。\nログイントークンが見つかりませんでした。");
        return;
    }

    document.write(`
<html>
<head><title>にらBOT</title></head>
<body>
<h1>下をコピー</h1>
<textarea id="target" style="width: 80%; height: 30%" readonly>
` + ltuid + `/` + ltoken + `
</textarea><br>
<button onclick="clipCopy()">コピー</button>
<h1>絶対にこの画面のスクリーンショットなどを他の人に見せないで下さい。</h1>
<div>HoyoLabに戻るにはページを更新するか<a href="https://www.hoyolab.com/">こちらからHoYoLABトップページに戻る</a></div>
<script>
const clipCopy = () => {
    var target = document.getElementById("target");
    target.select();
    document.execCommand("Copy");
    return;
}
</script>
</body>
</html>`);
}

main();

/* iOS Share Script用終了処理 */
try{
    completion();
} catch {
    console.log("Exit");
}