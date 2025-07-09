# SPDX-License-Identifier: BSD-3-Clause
# SPDX-FileCopyrightText: 2025 Rachel Mant <git@dragonmux.network>

# Define a project for OpenAL, marking it as needing C++17/C17
project(
	'openal',
	'cpp',
	default_options: [
		'c_std=c17',
		'cpp_std=c++17',
		'warning_level=3',
		'buildtype=release',
		'b_ndebug=if-release',
	],
	version: '1.24.3',
	meson_version: '>= 0.63',
	subproject_dir: 'deps',
	license: 'LGPL-2.0-only'
)

cxx = meson.get_compiler('cpp')

# Pull in lib{fmt} which is required for the logging system
fmt = subproject(
	'fmt',
	default_options: [
		'default_library=static',
	],
).get_variable(
	'fmt_dep'
)

# Start building configuration data to use with configure_file()
config = configuration_data()
# Along with what the build dependencies are, starting with fmt
dependencies = [fmt]

# Check to see if we're building for Windows
isWindows = host_machine.system() == 'windows'

# If we are building for Windows, then add a bunch of defines that are neded globally
if isWindows
	add_project_arguments(
		# Make sure the library knows we're on Windows
		'-D_WIN32',
		# Prevent windows.h from doing a stupid
		'-DNOMINMAX',
		language: 'cpp',
	)
	# Check if we're building against MinGW in some capacity
	if cxx.get_define('__MINGW32__') == '1'
		add_project_arguments('-D__USE_MINGW_ANSI_STDIO', language: 'cpp')
	endif
endif

# Check to see if we're building on something MSVC-like (handles clang-cl as well as MSVC)
if cxx.get_define('_MSC_VER') != ''
	add_project_arguments(
		# Tell the Windows CRT to not give warnings for "insecure" function usage
		'-D_CRT_SECURE_NO_WARNINGS',
		# Suppress a bug caused by a mismatch ebtween compiler and runtime with MSVC 2022 17.10 and newer
		'-D_DISABLE_CONSTEXPR_MUTEX_CONSTRUCTOR',
		cxx.get_supported_arguments(
			# Try to add `/permissive-` if at all possible
			'/permissive-',
			# Try to tell the compiler we're using UTF-8 source and strings
			'/utf-8',
		),
		# Disable some warnings (XXX: really?!)
		'/w14640',
		'/wd4065',
		'/wd4127',
		'/wd4268',
		'/wd4324',
		'/wd5030',
		'/wd5051',
		language: 'cpp',
	)

	exportStyle = '__declspec(dllexport)'
else
	add_project_arguments(
		# Try to add a bunch of arguments that may or may not be supported by the user's compiler
		# but which help with diagnostic output significantly
		cxx.get_supported_arguments(
			'-Winline',
			'-Wunused',
			'-Wshadow',
			'-Wconversion',
			'-Wcast-align',
			'-Wpedantic',
			'-Wold-style-cast',
			'-Wnon-virtual-dtor',
			'-Woverloaded-virtual',
			'-Wno-c++20-attribute-extensions',
			'-Wno-c++20-extensions',
			'-Wno-interference-size',
			# Add in flags too for compiler passes and help we want.
			# This one enables the equivilent of C++26's feature to initialise all locals with a non-0
			# bit pattern w/ [[gnu::uninitialized]] needed to disable this happening where necessary.
			'-ftrivial-auto-var-init=pattern',
			# Turn off errno for maths where possible
			'-fno-math-errno',
		),
		language: 'cpp',
	)

	if cxx.has_function_attribute('visibility:protected')
		exportStyle = '__attribute__((visibility("protected")))'
	elif cxx.has_function_attribute('visibility:default')
		exportStyle = '__attribute__((visibility("default")))'
	else
		exportStyle = ''
	endif
endif

haveSSE = cxx.check_header('xmmintrin.h')
haveSSE2 = haveSSE and cxx.check_header('emmintrin.h')
haveSSE3 = haveSSE2 and cxx.check_header('pmmintrin.h')
haveSSE4_1 = haveSSE3 and cxx.check_header('smmintrin.h')

haveNEON = cxx.check_header('arm_neon.h') and cxx.compiles('''
#include <arm_neon.h>
int main(int, char **)
{
	int32x4_t ret4 = vdupq_n_s32(0);
	return vgetq_lane_s32(ret4, 0);
}
''')

# Check to see if this system has libm and add it to our dependencies if it does
libm = cxx.find_library('m', required: false)
if libm.found() and cxx.has_function('pow', dependencies: libm)
	dependencies += libm
	config.set10('HAVE_LIBM', libm.found())
endif

# Check to see if this system has librt for clock_gettime
rt = cxx.find_library('rt', required: false)
if rt.found() and cxx.has_function('clock_gettime', dependencies: rt)
	dependencies += rt
	config.set10('HAVE_LIBRT', libm.found())
endif

# Check to see if this system has libdl & dlfcn.h for the dlopen() syscalls
dl = cxx.find_library(
	'dl',
	has_headers: 'dlfcn.h',
	required: false
)
if dl.found() and cxx.has_function('dlopen', dependencies: dl)
	dependencies += dl
	config.set10('HAVE_DLFCN_H', libm.found())
	config.set10('HAVE_LIBDL', libm.found())
endif

# Check to see if we have the guiddef.h header or not
config.set10('HAVE_GUIDDEF_H', cxx.check_header('guiddef.h'))

# Check to see if we have the cpuid.h header or not
if cxx.has_header('cpuid.h')
	config.set10('HAVE_CPUID_H', true)
	# Check to see if we have GCC's `__get_cpuid()` intrinsic
	config.set10(
		'HAVE_GCC_GET_CPUID',
		cxx.compiles('''
#include <cpuid.h>
int main()
{
	unsigned eax, ebx, ecx, edx;
	return __get_cpuid(0, &eax, &ebx, &ecx, &edx);
}
		''')
	)
endif

# Check to see if we have the intrin.h header or not
if cxx.has_header('intrin.h')
	config.set10('HAVE_INTRIN_H', true)
	# Check to see if we have the `__cpuid()` intrinsic
	config.set10(
		'HAVE_CPUID_INTRINSIC',
		cxx.compiles('''
#include <intrin.h>
int main()
{
	int regs[4];
	__cpuid(regs, 0);
	return regs[0];
}
		''')
	)
endif

config.set10(
	'HAVE_PROC_PIDPATH',
	cxx.has_header_symbol('libproc.h', 'proc_pidpath')
)

if not isWindows
	# pthreads is required on not-Windows - for things like semaphores.
	config.set10('HAVE_PTHREAD_H', cxx.check_header('pthread.h', required: true))
	# See if the compiler supports `-pthread`, and if it does, enforce it
	if cxx.has_argument('-pthread')
		config.set10('HAVE_PTHREAD', true)
		add_project_arguments('-pthread', language: 'cpp')
		add_project_link_arguments('-pthread', language: 'cpp')
	endif

	# Check to see if the scheduling parameter calls exist
	config.set10(
		'HAVE_PTHREAD_SETSCHEDPARAM',
		cxx.has_header_symbol('pthread.h', 'pthread_setschedparam')
	)

	# Check to see if we've got the pthread_np interfaces
	havePthreadNP = cxx.check_header(
		'pthread_np.h',
		prefix: '#include <pthread.h>',
	)
	config.set10('HAVE_PTHREAD_NP_H', havePthreadNP)
	# Check to see if pthread_setname_np exists in an appropriate header
	if havePthreadNP
		config.set10(
			'HAVE_PTHREAD_SETNAME_NP',
			cxx.has_header_symbol(
				'pthread_np.h',
				'pthread_setname_np',
				prefix: '#include <pthread.h>',
			)
		)
	else
		config.set10(
			'HAVE_PTHREAD_SETNAME_NP',
			cxx.has_header_symbol(
				'pthread.h',
				'pthread_setname_np',
			)
		)
	endif
endif

commonSrcs = files(
	'common/alassert.cpp',
	'common/alcomplex.cpp',
	'common/alsem.cpp',
	'common/alstring.cpp',
	'common/althrd_setname.cpp',
	'common/dynload.cpp',
	'common/filesystem.cpp',
	'common/pffft.cpp',
	'common/polyphase_resampler.cpp',
	'common/ringbuffer.cpp',
	'common/strutils.cpp',
)

coreSrcs = files(
	'core/ambdec.cpp',
	'core/ambidefs.cpp',
	'core/bformatdec.cpp',
	'core/bs2b.cpp',
	'core/bsinc_tables.cpp',
	'core/buffer_storage.cpp',
	'core/context.cpp',
	'core/converter.cpp',
	'core/cpu_caps.cpp',
	'core/cubic_tables.cpp',
	'core/devformat.cpp',
	'core/device.cpp',
	'core/effectslot.cpp',
	'core/except.cpp',
	'core/filters/biquad.cpp',
	'core/filters/nfc.cpp',
	'core/filters/splitter.cpp',
	'core/fpu_ctrl.cpp',
	'core/helpers.cpp',
	'core/hrtf.cpp',
	'core/logging.cpp',
	'core/mastering.cpp',
	'core/mixer.cpp',
	'core/storage_formats.cpp',
	'core/uhjfilter.cpp',
	'core/uiddefs.cpp',
	'core/voice.cpp',
	'core/mixer/mixer_c.cpp',
)

openALSrcs = files(
	'al/auxeffectslot.cpp',
	'al/buffer.cpp',
	'al/debug.cpp',
	'al/effect.cpp',
	'al/effects/autowah.cpp',
	'al/effects/chorus.cpp',
	'al/effects/compressor.cpp',
	'al/effects/convolution.cpp',
	'al/effects/dedicated.cpp',
	'al/effects/distortion.cpp',
	'al/effects/echo.cpp',
	'al/effects/effects.cpp',
	'al/effects/equalizer.cpp',
	'al/effects/fshifter.cpp',
	'al/effects/modulator.cpp',
	'al/effects/null.cpp',
	'al/effects/pshifter.cpp',
	'al/effects/reverb.cpp',
	'al/effects/vmorpher.cpp',
	'al/error.cpp',
	'al/event.cpp',
	'al/extension.cpp',
	'al/filter.cpp',
	'al/listener.cpp',
	'al/source.cpp',
	'al/state.cpp',
)

alcSrcs = files(
	'alc/alc.cpp',
	'alc/alu.cpp',
	'alc/alconfig.cpp',
	'alc/context.cpp',
	'alc/device.cpp',
	'alc/effects/autowah.cpp',
	'alc/effects/chorus.cpp',
	'alc/effects/compressor.cpp',
	'alc/effects/convolution.cpp',
	'alc/effects/dedicated.cpp',
	'alc/effects/distortion.cpp',
	'alc/effects/echo.cpp',
	'alc/effects/equalizer.cpp',
	'alc/effects/fshifter.cpp',
	'alc/effects/modulator.cpp',
	'alc/effects/null.cpp',
	'alc/effects/pshifter.cpp',
	'alc/effects/reverb.cpp',
	'alc/effects/vmorpher.cpp',
	'alc/events.cpp',
	'alc/panning.cpp',
)

backends = files(
	'alc/backends/base.cpp',
	'alc/backends/loopback.cpp',
	'alc/backends/null.cpp',
)

# Check to see if we can enable the PipeWire backend
pipewire = dependency(
	'libpipewire-0.3',
	version: '>=0.3.23',
	method: 'pkg-config',
	required: false
)
if pipewire.found()
	backends += files('alc/backends/pipewire.cpp')
	dependencies += pipewire
endif
config.set10('HAVE_PIPEWIRE', pipewire.found())

# Check to see if we can enable the PulseAudio backend
pulseAudio = dependency(
	'libpulse',
	method: 'pkg-config',
	required: false
)
if pulseAudio.found()
	backends += files('alc/backends/pulseaudio.cpp')
	dependencies += pulseAudio
endif
config.set10('HAVE_PULSEAUDIO', pulseAudio.found())

if not isWindows
	# Check to see if we can enable the ALSA backend
	alsa = dependency(
		'alsa',
		method: 'pkg-config',
		required: false
	)
	if alsa.found()
		backends += files('alc/backends/alsa.cpp')
		dependencies += alsa
	endif
	config.set10('HAVE_ALSA', alsa.found())

	# Check to see if we can enable the OSS backend
	if cxx.has_header('sys/soundcard.h')
		# See if there's a libossaudio to link against (it doesn't matter if there isn't!)
		ossLib = cxx.find_library(
			'ossaudio',
			required: false
		)
		backends += files('alc/backends/oss.cpp')
		dependencies += ossLib
		config.set10('HAVE_OSS', true)
	endif

	# Check to see if we can enable the Solaris audio backend
	if cxx.has_header('sys/audioio.h')
		backends += files('alc/backends/solaris.cpp')
		config.set10('HAVE_SOLARIS', true)
	endif

	# Check to see if we can enable the BSD SndIO backend
	sndIO = dependency(
		'sndio',
		method: 'pkg-config',
		required: false
	)
	if sndIO.found()
		backends += files('alc/backends/sndio.cpp')
		dependencies += sndIO
	endif
	config.set10('HAVE_SNDIO', sndIO.found())
else
	# Check to see if we can enable the WinMM backend
	winMM = cxx.find_library(
		'winmm',
		required: false
	)
	if winMM.found()
		backends += files('alc/backends/winmm.cpp')
		dependencies += winMM
	endif
	config.set10('HAVE_WINMM', winMM.found())

	# Check to see if we can enable the DirectSound backend
	dsound = cxx.find_library(
		'dsound',
		has_headers: ['dsound.h'],
		required: false
	)
	if dsound.found()
		backends += files('alc/backends/dsound.cpp')
		dependencies += dsound
	endif
	config.set10('HAVE_DSOUND', dsound.found())

	# Check to see if we can enable the WASAPI backend
	if cxx.has_header('mmdeviceapi.h')
		backends += files('alc/backends/wasapi.cpp')
	config.set10('HAVE_WASAPI', true)
	endif

	# Check to see if we can enable the OtherIO backend
	backends += files('alc/backends/otherio.cpp')
	config.set10('HAVE_OTHERIO', true)
endif

# Check to see if we can enable the JACK backend
jack = dependency(
	'jack',
	method: 'pkg-config',
	required: false
)
if jack.found()
	backends += files('alc/backends/jack.cpp')
	dependencies += jack
endif
config.set10('HAVE_JACK', jack.found())

# Check to see if we can enable the Apple CoreAudio backend
coreAudio = dependency(
	'CoreAudio',
	method: 'extraframework',
	required: false
)
if coreAudio.found()
	backends += files('alc/backends/coreaudio.cpp')
	dependencies += coreAudio
endif
config.set10('HAVE_COREAUDIO', coreAudio.found())

# Check to see if we can enable the Android Oboe backend
oboe = dependency(
	'oboe',
	required: false
)
if oboe.found()
	backends += files('alc/backends/oboe.cpp')
	dependencies += oboe
endif
config.set10('HAVE_OBOE', oboe.found())

# Check to see if we can enable the Android OpenSL backend
openSL = dependency(
	'OpenSLES',
	required: false
)
if openSL.found()
	backends += files('alc/backends/opensl.cpp')
	dependencies += openSL
endif
config.set10('HAVE_OPENSL', openSL.found())

# Check to see if we can enable the PortAudio backend
portAudio = dependency(
	'portaudio-2.0',
	method: 'pkg-config',
	required: false
)
if portAudio.found()
	backends += files('alc/backends/portaudio.cpp')
	dependencies += portAudio
endif
config.set10('HAVE_PORTAUDIO', portAudio.found())

# XXX: Need to gate these checks on whether to enable any SDL backends!
# # Check to see if we can enable the SDL3 backend
# sdl3 = dependency(
# 	'sdl3',
# 	method: 'pkg-config',
# 	required: false
# )
# if sdl3.found()
# 	backends += files('alc/backends/sdl3.cpp')
# 	dependencies += sdl3
# endif
# config.set10('HAVE_SDL3', sdl3.found())

# # Check to see if we can enable the SDL2 backend
# sdl2 = dependency(
# 	'sdl2',
# 	method: 'pkg-config',
# 	required: false
# )
# if sdl2.found()
# 	backends += files('alc/backends/sdl2.cpp')
# 	dependencies += sdl2
# endif
# config.set10('HAVE_SDL2', sdl2.found())

backends += files('alc/backends/wave.cpp')

configFiles = []

# See if `git` is available and where it is
git = find_program('git', required: false)
# If it was found, encode arguments for version.py
if git.found()
	gitParam = ['-g', git]
else
	gitParam = []
endif

# Build version.h so the library can know about the versioning information it needs
configFiles += custom_target(
	'version.h',
	# Find and run our versioning script to generate version.h
	command: [
		find_program('version.py', required: true),
		'-o', '@OUTPUT@',
		'-i', '@INPUT@',
		# Generate a tag file containing the `git describe` output to force this to re-run
		'-v', vcs_tag(
			command: [git, 'describe', '--always', '--tags', '--dirty'],
			input: '.version.in',
			output: '.version',
		)
	] + gitParam,
	input: 'version.h.in',
	output: 'version.h',
)

# Build config.h so the library knows its base configuration
configFiles += configure_file(
	input: 'config.h.in',
	output: 'config.h',
	format: 'cmake',
	configuration: config
)

# Build config_simd.h so the library knows the SIMD environment
configFiles += configure_file(
	input: 'config_simd.h.in',
	output: 'config_simd.h',
	format: 'cmake',
	configuration: config
)

# Build config_backends.h so the library knows which backends are enabled
configFiles += configure_file(
	input: 'config_backends.h.in',
	output: 'config_backends.h',
	format: 'cmake',
	configuration: config
)

if isWindows
	libName = 'OpenAL32'
else
	libName = 'openal'
endif

# alsoftCommon = static_library(
# 	'alsoft.common',
# 	commonSrcs,,
# 	include_directories: include_directories(
# 		'.',
# 		'common',
# 	),
# 	dependencies: dependencies,
# 	pic: true,
# )

# Build the main library and all the backends etc
openAL = library(
	'OpenAL',
	commonSrcs,
	openALSrcs,
	alcSrcs,
	backends,
	coreSrcs,
	configFiles,
	cpp_args: [
		'-DAL_ALEXT_PROTOTYPES',
		'-DAL_BUILD_LIBRARY',
		'-DOpenAL_EXPORTS',
		f'-DAL_API=@exportStyle@',
		f'-DALC_API=@exportStyle@',
	],
	cpp_static_args: '-DAL_LIBTYPE_STATIC',
	include_directories: include_directories(
		'.',
		'common',
		'include',
	),
	dependencies: dependencies,
	pic: true,
)

# Generate the openal.pc pkg-config file
pkgconfig = import('pkgconfig')
pkgconfig.generate(
	openAL,
	name: 'OpenAL',
	version: meson.project_version(),
	description: 'OpenAL is a cross-platform 3D audio API',
)

# Install all the public headers where they're expected
install_headers(
	'include/AL/al.h',
	'include/AL/alc.h',
	'include/AL/alext.h',
	'include/AL/efx.h',
	'include/AL/efx-presets.h',
	subdir: 'AL'
)

# Define a dependency for subproject usage
openalDep = declare_dependency(
	link_with: openAL,
	include_directories: include_directories(
		'include',
		'include/AL',
	),
)
