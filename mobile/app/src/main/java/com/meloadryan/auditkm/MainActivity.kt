package com.meloadryan.auditkm

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.SystemBarStyle
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.PathEffect
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.scale
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.meloadryan.auditkm.ui.theme.AuditKmTheme

private val Navy = Color(0xFF102C4C)
private val Teal = Color(0xFF23CDBD)
private val DarkTeal = Color(0xFF00867F)
private val PageBackground = Color(0xFFF1F4F8)
private val FieldBackground = Color(0xFFF7F9FC)
private val BorderColor = Color(0xFFCCD7E6)
private val MainText = Color(0xFF141D30)
private val SecondaryText = Color(0xFF53647C)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        enableEdgeToEdge(
            statusBarStyle = SystemBarStyle.dark(
                0xFF102C4C.toInt()
            ),
            navigationBarStyle = SystemBarStyle.light(
                0xFFF1F4F8.toInt(),
                0xFF102C4C.toInt()
            )
        )

        setContent {
            AuditKmTheme {
                LoginScreen()
            }
        }
    }
}

@Composable
private fun LoginScreen() {
    var username by rememberSaveable { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var passwordVisible by remember { mutableStateOf(false) }

    val focusManager = LocalFocusManager.current

    val fieldColors = OutlinedTextFieldDefaults.colors(
        focusedTextColor = MainText,
        unfocusedTextColor = MainText,
        cursorColor = DarkTeal,
        focusedBorderColor = DarkTeal,
        unfocusedBorderColor = BorderColor,
        focusedContainerColor = FieldBackground,
        unfocusedContainerColor = FieldBackground,
        focusedPlaceholderColor = SecondaryText,
        unfocusedPlaceholderColor = SecondaryText
    )

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(PageBackground)
    ) {
        HeaderBackground()

        Column(
            modifier = Modifier
                .align(Alignment.TopCenter)
                .widthIn(max = 480.dp)
                .fillMaxSize()
                .statusBarsPadding()
                .navigationBarsPadding()
                .imePadding()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 16.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(232.dp)
                    .padding(top = 16.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                AuditKmIcon(
                    modifier = Modifier.size(76.dp)
                )

                Spacer(modifier = Modifier.height(12.dp))

                Text(
                    text = buildAnnotatedString {
                        withStyle(
                            SpanStyle(
                                color = Color.White,
                                fontWeight = FontWeight.Bold
                            )
                        ) {
                            append("Audit")
                        }

                        withStyle(
                            SpanStyle(
                                color = Teal,
                                fontWeight = FontWeight.Bold
                            )
                        ) {
                            append("Km")
                        }
                    },
                    fontSize = 32.sp,
                    letterSpacing = (-1).sp
                )

                Spacer(modifier = Modifier.height(6.dp))

                Text(
                    text = "Controle, rastreamento e auditoria de deslocamentos",
                    modifier = Modifier.widthIn(max = 300.dp),
                    color = Color(0xFFCEDAE7),
                    fontSize = 14.sp,
                    lineHeight = 20.sp,
                    textAlign = TextAlign.Center
                )
            }

            Surface(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(28.dp),
                color = Color.White,
                shadowElevation = 6.dp
            ) {
                Column(
                    modifier = Modifier.padding(24.dp)
                ) {
                    Text(
                        text = "Bem-vindo de volta",
                        color = MainText,
                        fontSize = 25.sp,
                        fontWeight = FontWeight.Bold
                    )

                    Spacer(modifier = Modifier.height(6.dp))

                    Text(
                        text = "Entre com suas credenciais para continuar.",
                        color = SecondaryText,
                        fontSize = 14.sp,
                        lineHeight = 20.sp
                    )

                    Spacer(modifier = Modifier.height(24.dp))

                    FieldLabel("Usuário")

                    Spacer(modifier = Modifier.height(6.dp))

                    OutlinedTextField(
                        value = username,
                        onValueChange = { username = it },
                        modifier = Modifier.fillMaxWidth(),
                        singleLine = true,
                        shape = RoundedCornerShape(14.dp),
                        colors = fieldColors,
                        placeholder = {
                            Text(
                                text = "Digite seu usuário",
                                fontSize = 15.sp
                            )
                        },
                        leadingIcon = {
                            FieldSymbol(isPassword = false)
                        },
                        keyboardOptions = KeyboardOptions(
                            keyboardType = KeyboardType.Text,
                            imeAction = ImeAction.Next
                        ),
                        keyboardActions = KeyboardActions(
                            onNext = {
                                focusManager.moveFocus(
                                    androidx.compose.ui.focus.FocusDirection.Down
                                )
                            }
                        )
                    )

                    Spacer(modifier = Modifier.height(20.dp))

                    FieldLabel("Senha")

                    Spacer(modifier = Modifier.height(6.dp))

                    OutlinedTextField(
                        value = password,
                        onValueChange = { password = it },
                        modifier = Modifier.fillMaxWidth(),
                        singleLine = true,
                        shape = RoundedCornerShape(14.dp),
                        colors = fieldColors,
                        placeholder = {
                            Text(
                                text = "Digite sua senha",
                                fontSize = 15.sp
                            )
                        },
                        leadingIcon = {
                            FieldSymbol(isPassword = true)
                        },
                        trailingIcon = {
                            TextButton(
                                onClick = {
                                    passwordVisible = !passwordVisible
                                },
                                contentPadding = PaddingValues(
                                    horizontal = 8.dp
                                )
                            ) {
                                Text(
                                    text = if (passwordVisible) {
                                        "Ocultar"
                                    } else {
                                        "Mostrar"
                                    },
                                    color = SecondaryText,
                                    fontSize = 11.sp
                                )
                            }
                        },
                        visualTransformation = if (passwordVisible) {
                            VisualTransformation.None
                        } else {
                            PasswordVisualTransformation()
                        },
                        keyboardOptions = KeyboardOptions(
                            keyboardType = KeyboardType.Password,
                            imeAction = ImeAction.Done
                        ),
                        keyboardActions = KeyboardActions(
                            onDone = {
                                focusManager.clearFocus()
                            }
                        )
                    )

                    Spacer(modifier = Modifier.height(12.dp))

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Checkbox(
                            checked = false,
                            onCheckedChange = null,
                            enabled = false,
                            modifier = Modifier.size(24.dp)
                        )

                        Spacer(modifier = Modifier.width(6.dp))

                        Text(
                            text = "Lembrar de mim",
                            color = SecondaryText,
                            fontSize = 12.sp,
                            modifier = Modifier.weight(1f)
                        )

                        TextButton(
                            onClick = {},
                            enabled = false,
                            contentPadding = PaddingValues(
                                horizontal = 0.dp
                            ),
                            colors = ButtonDefaults.textButtonColors(
                                disabledContentColor = DarkTeal
                            )
                        ) {
                            Text(
                                text = "Esqueci minha senha",
                                fontSize = 12.sp,
                                fontWeight = FontWeight.SemiBold
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(20.dp))

                    Button(
                        onClick = {},
                        enabled = false,
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(56.dp),
                        shape = RoundedCornerShape(14.dp),
                        colors = ButtonDefaults.buttonColors(
                            disabledContainerColor = Navy,
                            disabledContentColor = Color.White
                        )
                    ) {
                        Text(
                            text = "Entrar",
                            fontSize = 16.sp,
                            fontWeight = FontWeight.Bold
                        )

                        Spacer(modifier = Modifier.width(12.dp))

                        Text(
                            text = "→",
                            color = Teal,
                            fontSize = 22.sp
                        )
                    }

                    Spacer(modifier = Modifier.height(12.dp))

                    OutlinedButton(
                        onClick = {},
                        enabled = false,
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(52.dp),
                        shape = RoundedCornerShape(14.dp),
                        border = BorderStroke(
                            width = 1.dp,
                            color = BorderColor
                        ),
                        colors = ButtonDefaults.outlinedButtonColors(
                            disabledContentColor = Navy
                        )
                    ) {
                        Text(
                            text = "Entrar com biometria",
                            fontSize = 14.sp,
                            fontWeight = FontWeight.SemiBold
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(36.dp))

            Text(
                text = "AuditKm · Gestão inteligente de frota",
                color = SecondaryText,
                fontSize = 12.sp,
                textAlign = TextAlign.Center
            )

            Spacer(modifier = Modifier.height(24.dp))
        }
    }
}

@Composable
private fun FieldLabel(text: String) {
    Text(
        text = text,
        color = SecondaryText,
        fontSize = 13.sp,
        fontWeight = FontWeight.SemiBold
    )
}

@Composable
private fun AuditKmIcon(modifier: Modifier = Modifier) {
    Canvas(
        modifier = modifier.semantics {
            contentDescription = "AuditKm, localização e auditoria"
        }
    ) {
        scale(
            scaleX = size.width / 100f,
            scaleY = size.height / 100f,
            pivot = Offset.Zero
        ) {
            drawRoundRect(
                color = Color(0xFF173657),
                size = Size(100f, 100f),
                cornerRadius = CornerRadius(25f, 25f)
            )

            val pin = Path().apply {
                moveTo(60f, 13f)
                cubicTo(44f, 13f, 33f, 25f, 33f, 40f)
                cubicTo(33f, 53f, 48f, 67f, 60f, 76f)
                cubicTo(72f, 67f, 87f, 53f, 87f, 40f)
                cubicTo(87f, 25f, 76f, 13f, 60f, 13f)
                close()
            }

            drawPath(pin, color = Teal)

            val check = Path().apply {
                moveTo(49f, 39f)
                lineTo(58f, 48f)
                lineTo(73f, 31f)
            }

            drawPath(
                path = check,
                color = Navy,
                style = Stroke(
                    width = 6f,
                    cap = StrokeCap.Round
                )
            )

            drawCircle(
                color = Color.White,
                radius = 4.5f,
                center = Offset(20f, 84f)
            )

            drawCircle(
                color = Color.White,
                radius = 2.7f,
                center = Offset(33f, 81f)
            )

            drawCircle(
                color = Color.White,
                radius = 2.5f,
                center = Offset(44f, 76f)
            )

            drawCircle(
                color = Color.White,
                radius = 2.3f,
                center = Offset(53f, 69f)
            )
        }
    }
}

@Composable
private fun HeaderBackground() {
    Canvas(
        modifier = Modifier
            .fillMaxWidth()
            .height(300.dp)
            .background(Navy)
    ) {
        val route = Path().apply {
            moveTo(0f, size.height * 0.82f)

            cubicTo(
                size.width * 0.22f,
                size.height * 0.62f,
                size.width * 0.32f,
                size.height,
                size.width * 0.57f,
                size.height * 0.72f
            )

            cubicTo(
                size.width * 0.77f,
                size.height * 0.46f,
                size.width * 0.82f,
                size.height * 0.36f,
                size.width,
                size.height * 0.49f
            )
        }

        drawPath(
            path = route,
            color = Teal.copy(alpha = 0.28f),
            style = Stroke(
                width = 2.dp.toPx(),
                cap = StrokeCap.Round,
                pathEffect = PathEffect.dashPathEffect(
                    floatArrayOf(
                        2.dp.toPx(),
                        8.dp.toPx()
                    )
                )
            )
        )

        drawCircle(
            color = Teal.copy(alpha = 0.4f),
            radius = 4.dp.toPx(),
            center = Offset(
                size.width * 0.85f,
                size.height * 0.42f
            )
        )
    }
}

@Composable
private fun FieldSymbol(isPassword: Boolean) {
    Canvas(modifier = Modifier.size(22.dp)) {
        val strokeWidth = 1.6.dp.toPx()

        if (isPassword) {
            drawRoundRect(
                color = SecondaryText,
                topLeft = Offset(
                    size.width * 0.2f,
                    size.height * 0.43f
                ),
                size = Size(
                    size.width * 0.6f,
                    size.height * 0.45f
                ),
                cornerRadius = CornerRadius(
                    2.dp.toPx(),
                    2.dp.toPx()
                ),
                style = Stroke(width = strokeWidth)
            )

            val shackle = Path().apply {
                moveTo(
                    size.width * 0.34f,
                    size.height * 0.43f
                )

                lineTo(
                    size.width * 0.34f,
                    size.height * 0.28f
                )

                cubicTo(
                    size.width * 0.34f,
                    size.height * 0.02f,
                    size.width * 0.66f,
                    size.height * 0.02f,
                    size.width * 0.66f,
                    size.height * 0.28f
                )

                lineTo(
                    size.width * 0.66f,
                    size.height * 0.43f
                )
            }

            drawPath(
                path = shackle,
                color = SecondaryText,
                style = Stroke(width = strokeWidth)
            )
        } else {
            drawCircle(
                color = SecondaryText,
                radius = size.width * 0.17f,
                center = Offset(
                    size.width * 0.5f,
                    size.height * 0.28f
                ),
                style = Stroke(width = strokeWidth)
            )

            val shoulders = Path().apply {
                moveTo(
                    size.width * 0.2f,
                    size.height * 0.88f
                )

                cubicTo(
                    size.width * 0.2f,
                    size.height * 0.46f,
                    size.width * 0.8f,
                    size.height * 0.46f,
                    size.width * 0.8f,
                    size.height * 0.88f
                )
            }

            drawPath(
                path = shoulders,
                color = SecondaryText,
                style = Stroke(
                    width = strokeWidth,
                    cap = StrokeCap.Round
                )
            )
        }
    }
}

@Preview(
    showBackground = true,
    widthDp = 390,
    heightDp = 844
)
@Composable
private fun LoginPreview() {
    AuditKmTheme {
        LoginScreen()
    }
}