export function Disclaimer() {
  return (
    <footer
      style={{
        marginTop: "2rem",
        paddingTop: "1rem",
        borderTop: "1px dashed #cfc7bc",
        fontSize: "0.85rem",
        color: "#5c534a",
      }}
    >
      <p style={{ margin: "0 0 0.5rem" }}>
        本工具在本地运行；请勿将敏感密钥提交到公开仓库。生成内容由模型产出，请自行核对事实后再投递。
      </p>
      <p style={{ margin: 0 }}>
        © {new Date().getFullYear()} Resume Optimizer（本地版）
      </p>
    </footer>
  );
}
