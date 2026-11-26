// SPDX-License-Identifier: Apache-2.0
plugins { id("media3.android-application") }

android {
    namespace = "org.fingmi.mpvprobe"
    defaultConfig {
        applicationId = "org.fingmi.mpvprobe"
        minSdk = 24
        targetSdk = 34
        testApplicationId = "org.fingmi.mpvprobe.test"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }
    testOptions.execution = "HOST"
}

dependencies {
    implementation(project(":lib-datasource-okhttp"))
    implementation(libs.androidx.annotation)
    implementation("com.squareup.okhttp3:okhttp:4.12.0") { version { strictly("4.12.0") } }
    androidTestImplementation(libs.androidx.test.runner)
    androidTestImplementation(libs.junit)
    androidTestImplementation("com.squareup.okhttp3:mockwebserver:4.12.0") { version { strictly("4.12.0") } }
}
