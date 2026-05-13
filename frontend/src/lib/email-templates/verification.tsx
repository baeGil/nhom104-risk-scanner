interface VerificationEmailProps {
  otpCode: string;
  userName: string;
  verifyUrl: string;
  expiryMinutes: number;
}

export function generateVerificationEmail({
  otpCode,
  userName,
  verifyUrl,
  expiryMinutes,
}: VerificationEmailProps): { subject: string; html: string } {
  const brandColor = "#2563eb";
  const appName = "PhápLý";

  const html = `
<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Xác thực email - ${appName}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f5f5f5; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 40px 0;">
    <tr>
      <td align="center">
        <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
          <!-- Header -->
          <tr>
            <td style="background-color: ${brandColor}; padding: 32px 40px; text-align: center;">
              <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 700;">
                ${appName}
              </h1>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding: 40px;">
              <h2 style="margin: 0 0 16px 0; color: #1a1a1a; font-size: 22px;">
                Xác thực email
              </h2>

              <p style="margin: 0 0 24px 0; color: #4a4a4a; font-size: 16px; line-height: 1.6;">
                Chào <strong>${userName}</strong>,
              </p>

              <p style="margin: 0 0 24px 0; color: #4a4a4a; font-size: 16px; line-height: 1.6;">
                Cảm ơn bạn đã đăng ký tài khoản ${appName}. Vui lòng sử dụng mã dưới đây để xác thực email:
              </p>

              <!-- OTP Code Block -->
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin: 32px 0;">
                <tr>
                  <td style="background-color: #1e1e1e; border-radius: 8px; padding: 20px 24px;">
                    <p style="margin: 0 0 8px 0; color: #9ca3af; font-size: 12px; font-family: monospace; text-transform: uppercase; letter-spacing: 1px;">
                      Mã xác thực
                    </p>
                    <p style="margin: 0; color: #ffffff; font-size: 32px; font-weight: 700; font-family: 'Courier New', Courier, monospace; letter-spacing: 8px; user-select: all; -webkit-user-select: all; -moz-user-select: all; -ms-user-select: all;">
                      ${otpCode}
                    </p>
                  </td>
                </tr>
              </table>

              <p style="margin: 16px 0 0 0; color: #9ca3af; font-size: 13px; text-align: center;">
                Bôi đen mã bên trên và copy (Ctrl+C / Cmd+C)
              </p>

              <p style="margin: 24px 0 0 0; color: #6b7280; font-size: 14px; text-align: center;">
                Mã có hiệu lực trong <strong>${expiryMinutes} phút</strong>
              </p>

              <!-- Divider -->
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin: 32px 0;">
                <tr>
                  <td style="border-top: 1px solid #e5e7eb; padding-top: 16px; text-align: center; color: #9ca3af; font-size: 14px;">
                    hoặc
                  </td>
                </tr>
              </table>

              <!-- CTA Button -->
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin: 24px 0;">
                <tr>
                  <td align="center">
                    <a href="${verifyUrl}" style="display: inline-block; background-color: ${brandColor}; color: #ffffff; padding: 14px 32px; text-decoration: none; border-radius: 8px; font-size: 16px; font-weight: 600;">
                      Xác thực email
                    </a>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background-color: #f8f9fa; padding: 24px 40px; border-top: 1px solid #e5e7eb;">
              <p style="margin: 0 0 8px 0; color: #6b7280; font-size: 13px; line-height: 1.5;">
                Nếu bạn không tạo tài khoản này, vui lòng bỏ qua email này.
              </p>
              <p style="margin: 0; color: #9ca3af; font-size: 12px;">
                © ${new Date().getFullYear()} ${appName}. All rights reserved.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
  `.trim();

  return {
    subject: `Xác thực email - ${appName}`,
    html,
  };
}
