#!/usr/bin/ruby

# Get the base directory
baseDir=File.expand_path('../..',__FILE__)

# Add bin directory to require search path
$LOAD_PATH.unshift "#{baseDir}/bin"

# Load libs
require 'yaml'
require 'date'
require 'fileutils'
require 'leadTime.rb'

# Load the experiment config
expConfig = YAML.load_file(ARGV[0])

# Get the assimilation type (3d, 4d)
assimilationType = expConfig['Assimilation']['Type']
assimilationAlgorithm = expConfig['Assimilation']['Algorithm']

# Get the analysis time
anlString=ARGV[1]
anlTime=DateTime.parse(anlString).to_time

# Load the base assimilation config template
assimConfig = YAML.load_file("#{baseDir}/yaml/#{assimilationType}.#{assimilationAlgorithm}.yaml")

# Create experiment assimilation output directory
expDir = "#{baseDir}/experiments/#{expConfig['Experiment']['Name']}"
fcstDir = "#{expDir}/forecasts/#{anlString}/assimilation_on"
FileUtils.mkdir_p("#{fcstDir}")

# Set up the assimilation window configuration
assimConfig["cost_function"]["window_begin"] = (anlTime + LeadTime.fcstToSeconds(expConfig['Assimilation']['Window Begin'])).strftime("%Y-%m-%dT%H:%M:%SZ")
assimConfig["cost_function"]["window_length"] = expConfig['Assimilation']['Window Length']

# Get the previous cycle
prevCycle = (anlTime - LeadTime.fcstToSeconds(expConfig['Experiment']['Cycle Frequency'])).strftime("%Y-%m-%dT%H:%M:%SZ")

# Set up the background file configuration
# 4DVar background files must be at the beginning of the assimilation window
if (expConfig['Assimilation']['Type'] == '4dvar')
  bkgOffset = LeadTime.fcstToSeconds(expConfig['Assimilation']['Window Begin']) + LeadTime.fcstToSeconds(expConfig['Experiment']['Cycle Frequency'])
# 3DVar background files must be in the center of the assimilation window
else
  bkgOffset = LeadTime.fcstToSeconds(expConfig['Assimilation']['Window Begin']) + LeadTime.fcstToSeconds(expConfig['Experiment']['Cycle Frequency']) + (LeadTime.fcstToSeconds(expConfig['Assimilation']['Window Length']) / 2)
end
bkgDate = (anlTime - LeadTime.fcstToSeconds(expConfig['Experiment']['Cycle Frequency']) + bkgOffset).strftime("%Y-%m-%dT%H:%M:%SZ")
assimConfig["cost_function"]["Jb"]["Background"]["state"].each_with_index do |bkg, i|
  assimConfig["cost_function"]["Jb"]["Background"]["state"][i]["filename"] = "#{expDir}/forecasts/#{prevCycle}/assimilation_on/test.fc.#{prevCycle}.#{LeadTime.secondsToFcst(bkgOffset)}"
  assimConfig["cost_function"]["Jb"]["Background"]["state"][i]["date"] = bkgDate
end

# Set up the background covariance matrix configuration
assimConfig["cost_function"]["Jb"]["Covariance"]["date"] = anlString
assimConfig["cost_function"]["Jb"]["Covariance"]["covariance"] = "L95Error"

# Set up the observation file configuration
assimConfig["cost_function"]["Jo"]["ObsTypes"].each_with_index do |obsType, i|
  assimConfig["cost_function"]["Jo"]["ObsTypes"][i]["ObsData"]["ObsDataIn"]["filename"] = "#{expDir}/obs/l95.truth.#{assimilationType}.#{anlString}.obt"
  assimConfig["cost_function"]["Jo"]["ObsTypes"][i]["ObsData"]["ObsDataOut"]["filename"] = "#{fcstDir}/l95.#{assimilationType}.#{anlString}.obt"
end

# Set up output directory configuration
assimConfig["output"]["datadir"] = fcstDir

# Write out updated assimilation config
FileUtils.mkdir_p("#{expDir}/yaml")
File.open("#{expDir}/yaml/#{assimilationType}.#{assimilationAlgorithm}.#{anlTime.strftime("%Y-%m-%dT%H:%M:%SZ")}.yaml", "w") { |f| YAML.dump(assimConfig, f) }

# Save the experiment config
File.open("#{expDir}/yaml/#{expConfig['Experiment']['Name']}.yaml", "w") { |f| YAML.dump(expConfig, f) }

# Run the assimilation
system("#{expConfig['JEDI Path']}/bin/l95_4dvar.x #{expDir}/yaml/#{assimilationType}.#{assimilationAlgorithm}.#{anlTime.strftime("%Y-%m-%dT%H:%M:%SZ")}.yaml > #{fcstDir}/runAssimilation.stdout")

if $?.exitstatus != 0
  raise "runAssimilation failed!  See #{fcstDir}/runAssimilation.stdout"
end
