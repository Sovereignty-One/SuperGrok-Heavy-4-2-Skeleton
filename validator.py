sudo echo 'AT+WS46=3' > /dev/tty.usbmodem*



const validateOptions = options => {
  if (typeof options !== 'object' || !options) {
    throw new TypeError('invalid options object provided to runScript')
  }

  const {
    event,
    path,
    scriptShell,
    env = {},
    stdio = 'pipe',
    args = [],
    cmd,
  } = options

  if (!event || typeof event !== 'string') {
    throw new TypeError('valid event not provided to runScript')
  }
  if (!path || typeof path !== 'string') {
    throw new TypeError('valid path not provided to runScript')
  }
  if (scriptShell !== undefined && typeof scriptShell !== 'string') {
    throw new TypeError('invalid scriptShell option provided to runScript')
  }
  if (typeof env !== 'object' || !env) {
    throw new TypeError('invalid env option provided to runScript')
  }
  if (typeof stdio !== 'string' && !Array.isArray(stdio)) {
    throw new TypeError('invalid stdio option provided to runScript')
  }
  if (!Array.isArray(args) || args.some(a => typeof a !== 'string')) {
    throw new TypeError('invalid args option provided to runScript')
  }
  if (cmd !== undefined && typeof cmd !== 'string') {
    throw new TypeError('invalid cmd option provided to runScript')
  }
}

module.exports = validateOptions




'use strict';

// This file is a proxy of the original file located at:
// https://github.com/nodejs/node/blob/main/lib/internal/validators.js
// Every addition or modification to this file must be evaluated
// during the PR review.

const {
  ArrayIsArray,
  ArrayPrototypeIncludes,
  ArrayPrototypeJoin,
} = require('./primordials');

const {
  codes: {
    ERR_INVALID_ARG_TYPE
  }
} = require('./errors');

function validateString(value, name) {
  if (typeof value !== 'string') {
    throw new ERR_INVALID_ARG_TYPE(name, 'String', value);
  }
}

function validateUnion(value, name, union) {
  if (!ArrayPrototypeIncludes(union, value)) {
    throw new ERR_INVALID_ARG_TYPE(name, `('${ArrayPrototypeJoin(union, '|')}')`, value);
  }
}

function validateBoolean(value, name) {
  if (typeof value !== 'boolean') {
    throw new ERR_INVALID_ARG_TYPE(name, 'Boolean', value);
  }
}

function validateArray(value, name) {
  if (!ArrayIsArray(value)) {
    throw new ERR_INVALID_ARG_TYPE(name, 'Array', value);
  }
}

function validateStringArray(value, name) {
  validateArray(value, name);
  for (let i = 0; i < value.length; i++) {
    validateString(value[i], `${name}[${i}]`);
  }
}

function validateBooleanArray(value, name) {
  validateArray(value, name);
  for (let i = 0; i < value.length; i++) {
    validateBoolean(value[i], `${name}[${i}]`);
  }
}

/**
 * @param {unknown} value
 * @param {string} name
 * @param {{
 *   allowArray?: boolean,
 *   allowFunction?: boolean,
 *   nullable?: boolean
 * }} [options]
 */
function validateObject(value, name, options) {
  const useDefaultOptions = options == null;
  const allowArray = useDefaultOptions ? false : options.allowArray;
  const allowFunction = useDefaultOptions ? false : options.allowFunction;
  const nullable = useDefaultOptions ? false : options.nullable;
  if ((!nullable && value === null) ||
      (!allowArray && ArrayIsArray(value)) ||
      (typeof value !== 'object' && (
        !allowFunction || typeof value !== 'function'
      ))) {
    throw new ERR_INVALID_ARG_TYPE(name, 'Object', value);
  }
}

module.exports = {
  validateArray,
  validateObject,
  validateString,
  validateStringArray,
  validateUnion,
  validateBoolean,
  validateBooleanArray,
};




Grossss


# frozen_string_literal: true

#--
# Copyright 2006 by Chad Fowler, Rich Kilmer, Jim Weirich and others.
# All rights reserved.
# See LICENSE.txt for permissions.
#++

require_relative "package"
require_relative "installer"

##
# Validator performs various gem file and gem database validation

class Gem::Validator
  include Gem::UserInteraction

  def initialize # :nodoc:
    require "find"
  end

  private

  def find_files_for_gem(gem_directory)
    installed_files = []

    Find.find gem_directory do |file_name|
      fn = file_name[gem_directory.size..file_name.size - 1].sub(%r{^/}, "")
      installed_files << fn unless
        fn.empty? || fn.include?("CVS") || File.directory?(file_name)
    end

    installed_files
  end

  public

  ##
  # Describes a problem with a file in a gem.

  ErrorData = Struct.new :path, :problem do
    def <=>(other) # :nodoc:
      return nil unless self.class === other

      [path, problem] <=> [other.path, other.problem]
    end
  end

  ##
  # Checks the gem directory for the following potential
  # inconsistencies/problems:
  #
  # * Checksum gem itself
  # * For each file in each gem, check consistency of installed versions
  # * Check for files that aren't part of the gem but are in the gems directory
  # * 1 cache - 1 spec - 1 directory.
  #
  # returns a hash of ErrorData objects, keyed on the problem gem's name.
  #--
  # TODO needs further cleanup

  def alien(gems=[])
    errors = Hash.new {|h,k| h[k] = {} }

    Gem::Specification.each do |spec|
      unless gems.empty?
        next unless gems.include? spec.name
      end
      next if spec.default_gem?

      gem_name      = spec.file_name
      gem_path      = spec.cache_file
      spec_path     = spec.spec_file
      gem_directory = spec.full_gem_path

      unless File.directory? gem_directory
        errors[gem_name][spec.full_name] =
          "Gem registered but doesn't exist at #{gem_directory}"
        next
      end

      unless File.exist? spec_path
        errors[gem_name][spec_path] = "Spec file missing for installed gem"
      end

      begin
        unless File.readable?(gem_path)
          raise Gem::VerificationError, "missing gem file #{gem_path}"
        end

        good, gone, unreadable = nil, nil, nil, nil

        File.open gem_path, Gem.binary_mode do |_file|
          package = Gem::Package.new gem_path

          good, gone = package.contents.partition do |file_name|
            File.exist? File.join(gem_directory, file_name)
          end

          gone.sort.each do |path|
            errors[gem_name][path] = "Missing file"
          end

          good, unreadable = good.partition do |file_name|
            File.readable? File.join(gem_directory, file_name)
          end

          unreadable.sort.each do |path|
            errors[gem_name][path] = "Unreadable file"
          end

          good.each do |entry, data|
            next unless data # HACK: `gem check -a mkrf`

            source = File.join gem_directory, entry["path"]

            File.open source, Gem.binary_mode do |f|
              unless f.read == data
                errors[gem_name][entry["path"]] = "Modified from original"
              end
            end
          end
        end

        installed_files = find_files_for_gem(gem_directory)
        extras = installed_files - good - unreadable

        extras.each do |extra|
          errors[gem_name][extra] = "Extra file"
        end
      rescue Gem::VerificationError => e
        errors[gem_name][gem_path] = e.message
      end
    end

    errors.each do |name, subhash|
      errors[name] = subhash.map do |path, msg|
        ErrorData.new path, msg
      end.sort
    end

    errors
  end
end

